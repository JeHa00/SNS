import pytest
from pydantic import ValidationError
from datetime import datetime, timedelta
from jose import jwt

from fastapi.encoders import jsonable_encoder

from sns.users.test.utils import random_lower_string, random_email
from sns.users.schema import UserCreate, UserUpdate
from sns.common.config import settings
from sns.users.service import (
    create_access_token,
    get_password_hash,
    get_current_user,
    verify_password,
    is_verified,
    get_user,
    create,
    update,
    delete,
)


@pytest.fixture(scope="function")
def fake_user(client, db_session):
    email = random_email()
    password = random_lower_string(k=8)
    user_info = UserCreate(email=email, password=password, password_confirm=password)
    user = create(db_session, user_info=user_info)
    return user


def test_create_access_token(client, db_session):
    data = {"email": random_email()}
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(data)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.SECRET_ALGORITHM
    )
    token = create_access_token(data)
    assert encoded_jwt == token


def test_create_user(client, db_session):
    email = random_email()
    password = random_lower_string(k=8)
    user_in = UserCreate(
        email=email, password=password, password_confirm=password, verified=False
    )
    user = create(db_session, user_info=user_in)

    assert user.email == email
    assert user.verified is False
    assert hasattr(user, "name")
    assert verify_password(password, user.password) is True

    password_below_minimum = random_lower_string(k=7)
    with pytest.raises(ValidationError):
        UserCreate(
            email=email,
            password=password_below_minimum,
            password_confirm=password_below_minimum,
            verified=False,
        )


def test_get_current_user(fake_user, db_session):
    data = {"sub": fake_user.email}
    token = create_access_token(data)
    payload = jwt.decode(token, settings.SECRET_KEY, settings.SECRET_ALGORITHM)
    email = payload.get("sub")

    user_01 = get_current_user(db_session, token)
    user_02 = get_user(db_session, email=email)

    assert user_02
    assert fake_user == user_01
    assert fake_user == user_02
    assert user_01 == user_02


def test_get_user(client, db_session):
    email = random_email()
    password = random_lower_string(k=8)
    user_info = UserCreate(email=email, password=password, password_confirm=password)
    user_created = create(db_session, user_info=user_info)

    user_by_only_email = get_user(db_session, email=user_info.email)
    assert user_by_only_email == user_created

    user_by_email_and_password = get_user(
        db_session, email=user_info.email, password=user_info.password
    )
    assert user_by_only_email == user_by_email_and_password


def test_update_user_on_being_verified(fake_user, db_session):
    old_verified = is_verified(fake_user)

    info_to_be_updated = UserUpdate(verified=True)
    update(db_session, fake_user, info_to_be_updated)
    user = get_user(db_session, email=fake_user.email)

    assert user
    assert jsonable_encoder(fake_user) == jsonable_encoder(user)
    assert old_verified is False
    assert is_verified(user) is True
    assert old_verified != is_verified(user)


def test_update_user_on_password(fake_user, db_session):
    old_password = fake_user.password

    info_to_be_updated = UserUpdate(
        password=get_password_hash(random_lower_string(k=8))
    )
    update(db_session, fake_user, info_to_be_updated)

    user = get_user(db_session, email=fake_user.email)
    new_password = user.password

    assert user
    assert jsonable_encoder(fake_user) == jsonable_encoder(user)
    assert old_password != new_password


def test_update_user_on_profile_text(fake_user, db_session):
    old_profile_text = fake_user.profile_text

    info_to_be_updated = UserUpdate(profile_text=f"{random_lower_string(k=10)}")
    update(db_session, fake_user, info_to_be_updated)

    user = get_user(db_session, email=fake_user.email)
    new_profile_text = user.profile_text

    assert user
    assert jsonable_encoder(fake_user) == jsonable_encoder(user)
    assert old_profile_text != new_profile_text


def test_delete_user(fake_user, db_session):
    delete(db_session, fake_user)
    user = get_user(db_session, email=fake_user.email)
    assert not user

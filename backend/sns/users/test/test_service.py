import pytest
from pydantic import ValidationError
from datetime import datetime, timedelta
from jose import jwt

from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException

from sns.users.test.utils import random_lower_string, random_email
from sns.users.schema import UserCreate, UserUpdate
from sns.common.config import settings
from sns.users.service import (
    get_current_user_verified,
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


def test_create_access_token(client, db_session):
    data = {"sub": random_email()}
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    data.update({"exp": expire})
    encoded_jwt = jwt.encode(
        data, settings.SECRET_KEY, algorithm=settings.SECRET_ALGORITHM
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
    assert hasattr(user, "profile_text")
    assert hasattr(user, "profile_image_name")
    assert hasattr(user, "profile_image_path")
    assert hasattr(user, "verified")
    assert hasattr(user, "verification_code")
    assert hasattr(user, "created_at")
    assert hasattr(user, "updated_at")
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
    user = fake_user.get("user")
    data = {"sub": user.email}
    token = create_access_token(data)
    payload = jwt.decode(token, settings.SECRET_KEY, settings.SECRET_ALGORITHM)
    email = payload.get("sub")

    user_01 = get_current_user(db_session, token)
    user_02 = get_user(db_session, email=email)

    assert user_02
    assert user == user_01
    assert user == user_02
    assert user_01 == user_02


def test_get_current_user_verified(fake_user, db_session):
    user = fake_user.get("user")
    info_to_be_updated = UserUpdate(verified=True)
    update(db_session, user, info_to_be_updated)
    verified_user = get_current_user_verified(user)
    assert verified_user == user


def test_get_current_user_not_verified(fake_user, db_session):
    user = fake_user.get("user")
    with pytest.raises(HTTPException):
        get_current_user_verified(user)


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
    user_01 = fake_user.get("user")
    old_verified = is_verified(user_01)

    info_to_be_updated = UserUpdate(verified=True)
    update(db_session, user_01, info_to_be_updated)
    user_02 = get_user(db_session, email=user_01.email)

    assert user_02
    assert jsonable_encoder(user_01) == jsonable_encoder(user_02)
    assert old_verified is False
    assert is_verified(user_02) is True
    assert old_verified != is_verified(user_02)


def test_update_user_on_password(fake_user, db_session):
    user_01 = fake_user.get("user")
    old_password = user_01.password

    info_to_be_updated = {"password": get_password_hash(random_lower_string(k=8))}
    update(db_session, user_01, info_to_be_updated)

    user_02 = get_user(db_session, email=user_01.email)
    new_password = user_02.password

    assert user_02
    assert jsonable_encoder(user_01) == jsonable_encoder(user_02)
    assert old_password != new_password


def test_update_user_on_profile_text(fake_user, db_session):
    user_01 = fake_user.get("user")
    old_profile_text = user_01.profile_text

    info_to_be_updated = UserUpdate(profile_text=f"{random_lower_string(k=10)}")
    update(db_session, user_01, info_to_be_updated)

    user_02 = get_user(db_session, email=user_01.email)
    new_profile_text = user_02.profile_text

    assert user_02
    assert jsonable_encoder(user_01) == jsonable_encoder(user_02)
    assert old_profile_text != new_profile_text


def test_delete_user(fake_user, db_session):
    user = fake_user.get("user")
    delete(db_session, user)
    user = get_user(db_session, email=user.email)
    assert not user

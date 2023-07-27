from typing import Dict

from fastapi.testclient import TestClient
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session
import pytest

from sns.users.test.utils import random_lower_string, random_email
from sns.users.schema import UserCreate, UserUpdate, UserPasswordUpdate
from sns.users.repositories.db import user_crud
from sns.users.service import user_service


def test_create_user_if_success(client: TestClient, db_session: Session):
    email = random_email()
    password = random_lower_string(k=8)
    hashed_password = user_service.get_password_hash(password)
    data_for_signup = UserCreate(
        email=email,
        password=hashed_password,
        password_confirm=hashed_password,
    ).dict()
    data_for_signup.pop("password_confirm")
    user = user_crud.create(db_session, **data_for_signup)
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
    assert user_service.verify_password(password, user.password) is True


def test_create_user_if_password_is_not_same_as_password_confirm(client: TestClient):
    # 서로 다른 password 생성
    password = random_lower_string(k=8)
    password_confirm = random_lower_string(k=8)

    while password == password_confirm:
        password = random_lower_string(k=8)
        password_confirm = random_lower_string(k=8)

    # 회원가입 정보
    with pytest.raises(ValidationError):
        UserCreate(
            email=random_email(),
            password=password,
            password_confirm=password_confirm,
            verified=False,
        )


def test_create_user_if_password_length_is_below_minimum_length(
    client: TestClient,
    db_session: Session,
):
    email = random_email()

    # 최소 글자 수보다 작은 패스워드 생성
    password_below_minimum = random_lower_string(k=7)

    with pytest.raises(ValidationError):
        UserCreate(
            email=email,
            password=password_below_minimum,
            password_confirm=password_below_minimum,
            verified=False,
        )


def test_get_user(client: TestClient, db_session: Session):
    email = random_email()
    password = random_lower_string(k=8)
    data_for_signup = UserCreate(
        email=email,
        password=password,
        password_confirm=password,
    ).dict()
    data_for_signup.pop("password_confirm")
    user_created = user_crud.create(db_session, **data_for_signup)

    user_by_only_email = user_crud.get_user(db_session, email=data_for_signup["email"])
    assert user_by_only_email == user_created


def test_update_user_on_being_verified(fake_user: Dict, db_session: Session):
    user_01 = fake_user.get("user")

    with pytest.raises(HTTPException):
        user_service.is_verified(user_01)

    previous_is_verified = False

    data_to_be_updated = {"verified": True}

    user_crud.update(db_session, user_01, **data_to_be_updated)
    user_02 = user_crud.get_user(db_session, email=user_01.email)

    assert user_02
    assert user_01 == user_02
    assert user_service.is_verified(user_02) is True
    assert previous_is_verified != user_service.is_verified(user_02)


def test_update_user_on_password(fake_user: Dict, db_session: Session):
    user_01 = fake_user.get("user")
    old_password = user_01.password

    password_to_be_updated = {"password": random_lower_string(k=8)}
    user_crud.update(db_session, user_01, **password_to_be_updated)

    user_02 = user_crud.get_user(db_session, email=user_01.email)
    new_password = user_02.password

    assert user_02
    assert user_01 == user_02
    assert old_password != new_password


def test_change_password_if_new_password_is_same_as_current_password(
    db_session: Session,
):
    password = random_lower_string(k=8)

    with pytest.raises(ValidationError):
        UserPasswordUpdate(
            current_password=password,
            new_password=password,
        )


def test_update_user_on_profile_text(fake_user: Dict, db_session: Session):
    user_01 = fake_user.get("user")
    old_profile_text = user_01.profile_text

    data_to_be_updated = UserUpdate(profile_text=f"{random_lower_string(k=10)}")
    user_crud.update(db_session, user_01, **data_to_be_updated.dict())

    user_02 = user_crud.get_user(db_session, email=user_01.email)
    new_profile_text = user_02.profile_text

    assert user_02
    assert user_01 == user_02
    assert old_profile_text != new_profile_text


def test_delete_user_by_int(fake_user: Dict, db_session: Session):
    user_01 = fake_user.get("user")
    email = user_01.email
    result = user_crud.remove(db_session, user_to_be_deleted=user_01.id)
    user_02 = user_crud.get_user(db_session, email=email)

    assert user_02 is None
    assert user_01 != user_02
    assert result == {"status": "success"}


def test_delete_user_by_model_object(fake_user: Dict, db_session: Session):
    user_01 = fake_user.get("user")
    email = user_01.email
    result = user_crud.remove(db_session, user_to_be_deleted=user_01)
    user_02 = user_crud.get_user(db_session, email=email)

    assert user_02 is None
    assert user_01 != user_02
    assert result == {"status": "success"}

from typing import Dict

import pytest
from fastapi.testclient import TestClient
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

# flake8: noqa
from sns.common.conftest import start_app, app, db_session, client

# flake8: noqa
from sns.users.test.conftest import fake_user, get_user_token_headers_and_user_info
from sns.users.test.utils import random_lower_string, random_email
from sns.users.schema import UserCreate
from sns.users.service import create
from sns.posts.schema import PostCreate, PostLike
from sns.posts.repository import post_crud, post_like_crud
from sns.posts import model


@pytest.fixture(scope="function")
def fake_post(client: TestClient, db_session: Session, fake_user: Dict) -> model.Post:
    content = random_lower_string(k=1000)
    post_info = PostCreate(content=content)
    user = fake_user.get("user")
    post = post_crud.create(db_session, post_info=post_info, writer_id=user.id)
    return post


@pytest.fixture(scope="function")
def fake_multi_posts(client: TestClient, db_session: Session, fake_user: Dict) -> None:
    post_total_count_to_make = 100

    while post_total_count_to_make > 0:
        content = random_lower_string(k=1000)
        post_info = PostCreate(content=content)
        user = fake_user.get("user")
        post_crud.create(db_session, post_info=post_info, writer_id=user.id)
        post_total_count_to_make -= 1


@pytest.fixture(scope="function")
def fake_postlike(
    client: TestClient, db_session: Session, fake_user: dict, fake_multi_posts
):
    # fake_user 정보 가져오기
    user = fake_user.get("user")

    # 또 다른 fake_user 생성
    password = random_lower_string(k=8)
    user_info = UserCreate(
        email=random_email(), password=password, password_confirm=password
    )
    another_user = create(db_session, user_info=user_info)

    for post_id in range(1, 51):
        like_info = PostLike(who_like_id=user.id, like_target_id=post_id)
        post_like_crud.like(db_session, like_info=jsonable_encoder(like_info))

    for post_id in range(1, 101):
        like_info = PostLike(who_like_id=another_user.id, like_target_id=post_id)
        post_like_crud.like(db_session, like_info=jsonable_encoder(like_info))

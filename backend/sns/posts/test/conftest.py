from typing import Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# flake8: noqa
from sns.common.conftest import start_app, app, db_session, client

# flake8: noqa
from sns.users.test.conftest import fake_user, get_user_token_headers_and_login_data
from sns.users.test.utils import random_lower_string, random_email
from sns.users.repositories.db import user_crud
from sns.users.schema import UserCreate, UserUpdate
from sns.posts.repository import post_crud, post_like_crud
from sns.posts.schema import PostCreate, PostLike
from sns.posts.model import Post


@pytest.fixture(scope="function")
def fake_post(client: TestClient, db_session: Session, fake_user: Dict) -> Post:
    """fake_user가 생성하는 한 개의 Post model를 만든다.

    Args:
        client (TestClient): test용 db url에 연결된 client를 생성
        db_session (Session): db session.
        fake_user (Dict): test용을 생성한 user 정보

    Returns:
        Post: 생성된 Post 객체를 반환
    """
    # user 정보
    user = fake_user.get("user")

    # verified 상태 변경
    data_to_be_updated = UserUpdate(verified=True)
    user_crud.update(db_session, user, data_to_be_updated)

    # 생성할 post 정보
    content = random_lower_string(k=1000)
    post_data = PostCreate(content=content)
    post = post_crud.create(db_session, post_data=post_data, writer_id=user.id)
    return post


@pytest.fixture(scope="function")
def fake_multi_posts(client: TestClient, db_session: Session, fake_user: Dict) -> None:
    """fake_user가 생성한 여러 개의 Post model를 만든다.

    Args:
        client (TestClient): test용 db url에 연결된 client를 생성
        db_session (Session): db session.
        fake_user (Dict): test용을 생성한 user 정보
    """
    post_total_count_to_make = 100

    while post_total_count_to_make > 0:
        content = random_lower_string(k=1000)
        post_data = PostCreate(content=content)
        user = fake_user.get("user")
        post_crud.create(db_session, post_data=post_data, writer_id=user.id)
        post_total_count_to_make -= 1


@pytest.fixture(scope="function")
def fake_post_by_user_logged_in(
    client: TestClient, db_session: Session, get_user_token_headers_and_login_data: dict
) -> Post:
    """로그인 상태의 유저가 생성한 post 한 개를 반환한다.

    Args:
        client (TestClient): test용 db url에 연결된 client를 생성
        db_session (Session): db session.
        get_user_token_headers_and_login_data (dict): 로그인된 user를 생성

    Returns:
        Post: 생성된 Post 객체를 반환
    """
    login_data = get_user_token_headers_and_login_data["login_data"]
    user = user_crud.get_user(db_session, login_data["email"])

    # 생성할 post 정보
    content = random_lower_string(k=1000)
    post_data = PostCreate(content=content)
    post = post_crud.create(db_session, post_data=post_data, writer_id=user.id)
    return post


@pytest.fixture(scope="function")
def fake_multi_post_by_user_logged_in(
    client: TestClient, db_session: Session, get_user_token_headers_and_login_data: dict
):
    """로그인 상태의 유저가 post 100개를 생성한다.

    Args:
        client (TestClient): test용 db url에 연결된 client를 생성
        db_session (Session): db session.
        get_user_token_headers_and_login_data (dict): 로그인된 user를 생성
    """
    login_data = get_user_token_headers_and_login_data["login_data"]
    user = user_crud.get_user(db_session, login_data["email"])
    post_total_count_to_make = 100

    while post_total_count_to_make > 0:
        content = random_lower_string(k=1000)
        post_data = PostCreate(content=content)
        post_crud.create(db_session, post_data=post_data, writer_id=user.id)
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
    another_user = user_crud.create(db_session, user_info=user_info)

    for post_id in range(1, 51):
        like_info = PostLike(who_like_id=user.id, like_target_id=post_id)
        post_like_crud.like(db_session, like_info=like_info)

    for post_id in range(1, 101):
        like_info = PostLike(who_like_id=another_user.id, like_target_id=post_id)
        post_like_crud.like(db_session, like_info=like_info)

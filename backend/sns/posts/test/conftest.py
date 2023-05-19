from typing import Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# flake8: noqa
from sns.common.conftest import start_app, app, db_session, client

# flake8: noqa
from sns.users.test.conftest import get_user_token_headers_and_user_info, fake_user
from sns.users.test.utils import random_lower_string
from sns.users.repositories.db import user_crud
from sns.users.schema import UserUpdate
from sns.posts.repository import post_crud
from sns.posts.schema import PostCreate
from sns.posts.model import Post


@pytest.fixture(scope="function")
def fake_post(
    client: TestClient,
    db_session: Session,
    fake_user: Dict,
) -> Post:
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
    user_crud.update(
        db_session,
        user=user,
        data_to_be_updated=data_to_be_updated,
    )

    # 생성할 post 정보
    content = random_lower_string(k=1000)
    post_data = PostCreate(content=content)
    post = post_crud.create(
        db_session,
        post_data=post_data,
        writer_id=user.id,
    )
    return post


@pytest.fixture(scope="function")
def fake_multi_posts(
    client: TestClient,
    db_session: Session,
    fake_user: Dict,
) -> None:
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
        post_crud.create(
            db_session,
            post_data=post_data,
            writer_id=user.id,
        )
        post_total_count_to_make -= 1


@pytest.fixture(scope="function")
def fake_post_by_user_logged_in(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: dict,
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
    post = post_crud.create(
        db_session,
        post_data=post_data,
        writer_id=user.id,
    )
    return post


@pytest.fixture(scope="function")
def fake_multi_post_by_user_logged_in(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: dict,
):
    """로그인 상태의 유저가 post 100개를 생성한다.

    Args:
        client (TestClient): test용 db url에 연결된 client를 생성
        db_session (Session): db session.
        get_user_token_headers_and_login_data (dict): 로그인된 user를 생성
    """
    login_data = get_user_token_headers_and_login_data["login_data"]
    user = user_crud.get_user(
        db_session,
        login_data["email"],
    )
    post_total_count_to_make = 100

    while post_total_count_to_make > 0:
        content = random_lower_string(k=1000)
        post_data = PostCreate(content=content)
        post_crud.create(
            db_session,
            post_data=post_data,
            writer_id=user.id,
        )
        post_total_count_to_make -= 1

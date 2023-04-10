from typing import Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from sns.common.conftest import app, db_session, client
from sns.users.test.utils import random_lower_string
from sns.users.test.conftest import fake_user
from sns.posts.schema import PostCreate
from sns.posts.repository import post_crud
from sns.posts.model import Post


@pytest.fixture(scope="function")
def fake_post(client: TestClient, db_session: Session, fake_user: Dict) -> Post:
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

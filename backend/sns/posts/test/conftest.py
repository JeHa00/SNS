from typing import List, Dict
import random
import string

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


from sns.common.conftest import app, db_session, client
from sns.users.test.utils import random_lower_string
from sns.users.test.conftest import fake_user
from sns.posts.schema import PostCreate
from sns.posts.service import create
from sns.posts.model import Post


@pytest.fixture(scope="function")
def fake_post(client: TestClient, db_session: Session, fake_user: Dict) -> Post:
    content = "".join(random.choices(string.ascii_lowercase, k=500))
    post_info = PostCreate(content=content)
    user = fake_user.get("user")
    post = create(db_session, post_info=post_info, writer_id=user.id)
    return post


@pytest.fixture(scope="function")
def fake_multi_posts(client: TestClient, db_session: Session, fake_user: Dict) -> None:
    post_total_count_to_make = 100

    while post_total_count_to_make > 0:
        content = "".join(random.choices(string.ascii_lowercase, k=1000))
        post_info = PostCreate(content=content)
        user = fake_user.get("user")
        create(db_session, post_info=post_info, writer_id=user.id)
        post_total_count_to_make -= 1

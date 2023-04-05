from typing import Dict, List
from random import randint

from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from fastapi import status
import pytest

from sns.common.config import settings
from sns.users.test.conftest import fake_user, get_user_token_headers_and_user_info
from sns.users.service import get_user
from sns.posts.service import get_post
from sns.posts.test.conftest import fake_post, fake_multi_posts
from sns.posts.schema import Post, PostCreate, PostUpdate
from sns.posts import model


@pytest.mark.read_post
def test_read_post_existed(
    client: TestClient, 
    db_session: Session,
    fake_multi_posts: None
):
    total_post_count = 100
    for post_id in range(1, total_post_count + 1):
        response = client.get(f"{settings.API_V1_STR}/posts/{post_id}")
        post = response.json()

        assert response.status_code == 200
        assert response != None
        assert post.get('id') == post_id


@pytest.mark.read_post
def test_read_post_not_existed(
    client: TestClient, 
    db_session: Session, 
    fake_post: model.Post
):
    post_id = randint(fake_post.id + 1, 100)
    response = client.get(f"{settings.API_V1_STR}/posts/{post_id}")
    result_msg = response.json().get("detail")

    assert response.status_code == 404
    assert result_msg == "해당 id의 포스트를 찾을 수 없습니다."


@pytest.mark.read_posts
def test_read_posts_if_not_registered():
    pass


@pytest.mark.read_posts
def test_read_posts_if_not_existed():
    pass 


@pytest.mark.read_posts
def test_read_posts_if_post_is_more_than_one():
    pass


@pytest.mark.delete_post
def test_delete_post_if_authorized(
    client: TestClient, 
    db_session: Session, 
    get_user_token_headers_and_user_info: Dict, 
    fake_post: model.Post,
):
    # user 및 post 정보
    headers = get_user_token_headers_and_user_info.get("headers")
    user_info = get_user_token_headers_and_user_info.get("user_info")
    user = get_user(db_session, email=user_info.get("email"))
    user_id = user.id
    post_id = fake_post.id

    # 글 삭제 및 결과
    response = client.delete(f"{settings.API_V1_STR}/users/{user_id}/posts/{post_id}", headers=headers)
    result_status_text = response.json().get("status")
    result_msg = response.json().get("msg")

    # 결과 확인
    post = get_post(db_session, post_id=post_id)

    assert response.status_code == status.HTTP_200_OK
    assert result_status_text == "success"
    assert result_msg == "글이 삭제되었습니다."
    assert post == None


@pytest.mark.delete_post
def test_delete_post_if_not_authorized(
    client: TestClient, 
    db_session: Session, 
    get_user_token_headers_and_user_info: Dict, 
    fake_post: model.Post, 
):
    # user 및 post 정보
    headers = get_user_token_headers_and_user_info.get("headers")
    user_id = 2
    post_id = fake_post.id

    # 글 삭제 및 결과
    response = client.delete(f"{settings.API_V1_STR}/users/{user_id}/posts/{post_id}", headers=headers)
    result_msg = response.json().get("detail")

    # 결과 확인
    post = get_post(db_session, post_id=post_id)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert result_msg == "삭제할 권한이 없습니다."
    assert post != None
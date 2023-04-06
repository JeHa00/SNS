from typing import Dict
from random import randint

from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from fastapi import status
import pytest

from sns.common.config import settings
from sns.users.test.conftest import fake_user, get_user_token_headers_and_user_info
from sns.users.test.utils import random_lower_string
from sns.users.service import get_user
from sns.posts.service import get_post
from sns.posts.test.conftest import fake_post, fake_multi_posts
from sns.posts.schema import PostCreate, PostUpdate
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
def test_read_posts_if_not_registered(client: TestClient):
    # 가짜 유저 id
    user_id = 1

    # 글 조회 및 결과
    response = client.get(f"{settings.API_V1_STR}/users/{user_id}/posts")
    result_msg = response.json().get("detail")

    assert response.status_code == 403
    assert result_msg == "등록되지 않은 유저입니다."


@pytest.mark.read_posts
def test_read_posts_if_post_not_exist(
    client: TestClient, 
    fake_user: Dict
):
    
    # 유저 정보
    user = fake_user.get("user")
    
    # 글 조회 및 결과
    response = client.get(f"{settings.API_V1_STR}/users/{user.id}/posts")
    result_msg = response.json().get("detail")

    assert response.status_code == 404 
    assert result_msg == "생성된 글이 없습니다."


@pytest.mark.read_posts
def test_read_posts_if_post_exist(
    client: TestClient, 
    fake_user: Dict, 
    fake_multi_posts: None
):
    
    # 유저 정보
    user = fake_user.get("user")

    # 글 조회 및 결과
    response = client.get(f"{settings.API_V1_STR}/users/{user.id}/posts")
    result = response.json()

    assert response.status_code == 200
    assert response != None
    assert len(result) == 100


@pytest.mark.create_post
def test_create_post_if_user_not_registered(
    client: TestClient, 
    db_session: Session,
    get_user_token_headers_and_user_info: Dict
):
    # current_user 정보
    headers = get_user_token_headers_and_user_info.get("headers")

    # 생성할 글 content 정보
    content = PostCreate(content=random_lower_string(k=1000))
    data = jsonable_encoder(content)

    # 등록되지 않은 유저 id
    not_registered_user_id = 2

    # 글 생성 및 결과
    response = client.post(
        f"{settings.API_V1_STR}/users/{not_registered_user_id}/posts", 
        headers=headers, 
        json=data)
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert result_msg == "등록된 회원이 아닙니다."


@pytest.mark.create_post
def test_create_post_if_unauthorized(
    client: TestClient, 
    db_session: Session, 
    fake_user: Dict,
    get_user_token_headers_and_user_info: Dict
):
    # current_user 정보
    headers = get_user_token_headers_and_user_info.get("headers")

    # 생성할 글 content 정보
    content = PostCreate(content=random_lower_string(k=1000))
    data = jsonable_encoder(content)

    # 인가받지 않은 user 정보
    unauthorized_user = fake_user.get("user")

    # 글 생성 및 결과
    response = client.post(
        f"{settings.API_V1_STR}/users/{unauthorized_user.id}/posts", 
        headers=headers, 
        json=data)
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert result_msg == "작성할 권한이 없습니다."


@pytest.mark.create_post
def test_create_post_if_authorized(
    client: TestClient, 
    db_session: Session,
    get_user_token_headers_and_user_info: Dict
):
    # current_user 정보
    headers = get_user_token_headers_and_user_info.get("headers")
    user_info = get_user_token_headers_and_user_info.get("user_info")
    authorized_user = get_user(db_session, email=user_info.get("email"))


    # 생성할 글 content 정보
    content = PostCreate(content=random_lower_string(k=1000))
    data = jsonable_encoder(content)

    # 글 생성 및 결과
    response = client.post(
        f"{settings.API_V1_STR}/users/{authorized_user.id}/posts", 
        headers=headers, 
        json=data)
    created_post_id = response.json().get("id")
    post = get_post(db_session, post_id=created_post_id)

    assert response.status_code == status.HTTP_201_CREATED
    assert post != None


@pytest.mark.update_post
def test_update_post_if_user_not_registered(
    client: TestClient, 
    get_user_token_headers_and_user_info: Dict, 
    fake_post: model.Post
):
    # current_user 정보
    headers = get_user_token_headers_and_user_info.get("headers")

    # 변경할 글 content 정보
    content = PostCreate(content=random_lower_string(k=1000))
    data = jsonable_encoder(content)

    # 등록되지 않은 유저 id
    not_registered_user_id = 3

    # 글 수정 및 결과
    response = client.put(
        f"{settings.API_V1_STR}/users/{not_registered_user_id}/posts/{fake_post.id}", 
        headers=headers, 
        json=data)
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert result_msg == "등록된 회원이 아닙니다."


@pytest.mark.update_post
def test_update_post_if_unauthorized(
    client: TestClient, 
    db_session: Session, 
    get_user_token_headers_and_user_info: Dict,
    fake_post: model.Post,
):
    # current_user 정보
    headers = get_user_token_headers_and_user_info.get("headers")
    user_info = get_user_token_headers_and_user_info.get("user_info")
    authorized_user = get_user(db_session, email=user_info.get("email"))

    # 변경할 content 정보
    content = PostCreate(content=random_lower_string(k=1000))
    data = jsonable_encoder(content)

    # 글 수정 및 결과
    response = client.post(
        f"{settings.API_V1_STR}/users/{authorized_user.id}/posts", 
        headers=headers, 
        json=data)
    created_post_id = response.json().get("id")
    post = get_post(db_session, post_id=created_post_id)

    assert response.status_code == status.HTTP_201_CREATED
    assert post != None


@pytest.mark.update_post
def test_update_post_if_post_not_exist(
    client: TestClient, 
    db_session: Session, 
    get_user_token_headers_and_user_info: Dict
):
    # current_user 정보
    headers = get_user_token_headers_and_user_info.get("headers")
    user_info = get_user_token_headers_and_user_info.get("user_info")
    authorized_user = get_user(db_session, email=user_info.get("email"))

    # 변경할 content 정보
    content = PostUpdate(content=random_lower_string(k=1000))
    data = jsonable_encoder(content)

    # 글 수정 및 결과
    response = client.put(
        f"{settings.API_V1_STR}/users/{authorized_user.id}/posts/{1}", 
        headers=headers, 
        json=data)
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_msg == "해당되는 글이 없습니다."


@pytest.mark.update_post
def test_update_post_only_one_if_authorized(
    client: TestClient, 
    db_session: Session, 
    get_user_token_headers_and_user_info: Dict,
    fake_post: model.Post, 
):
    # current_user 정보
    headers = get_user_token_headers_and_user_info.get("headers")
    user_info = get_user_token_headers_and_user_info.get("user_info")
    authorized_user = get_user(db_session, email=user_info.get("email"))

    # 변경할 content 정보
    content = PostUpdate(content=random_lower_string(k=1000))
    data = jsonable_encoder(content)

    # 글 수정 및 결과
    response = client.put(
        f"{settings.API_V1_STR}/users/{authorized_user.id}/posts/{fake_post.id}", 
        headers=headers, 
        json=data)
    content_updated = response.json().get("content")

    assert response.status_code == status.HTTP_200_OK
    assert content_updated == data.get("content")


@pytest.mark.update_post
def test_update_post_multi_posts_if_authorized(
    client: TestClient, 
    db_session: Session, 
    get_user_token_headers_and_user_info: Dict,
    fake_multi_posts: None,
):
    # current_user 정보
    headers = get_user_token_headers_and_user_info.get("headers")
    user_info = get_user_token_headers_and_user_info.get("user_info")
    authorized_user = get_user(db_session, email=user_info.get("email"))

    for post_id in range(1, 101):
        # 변경할 content 정보
        content = PostUpdate(content=random_lower_string(k=1000))
        data = jsonable_encoder(content)

        # 글 수정 및 결과
        response = client.put(
            f"{settings.API_V1_STR}/users/{authorized_user.id}/posts/{post_id}", 
            headers=headers, 
            json=data)
        result_content = response.json().get("content")
        result_id = response.json().get("id")

        assert response.status_code == status.HTTP_200_OK
        assert response != None
        assert result_content == data.get("content")
        assert result_id == post_id


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
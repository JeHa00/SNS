import pytest

from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session

from sns.common.config import settings
from sns.users.test.utils import random_lower_string, random_email
from sns.users.service import user_service
from sns.users.repositories.db import user_crud
from sns.users.schema import UserCreate
from sns.posts.model import Post
from sns.comments.model import Comment
from sns.comments.schema import CommentCreate, CommentUpdate


@pytest.mark.get_comments_on_a_post
def test_get_comments_on_a_post_if_post_not_exist(
    client: TestClient,
    db_session: Session,
):
    post_id = 1
    page = 1
    response = client.get(
        f"{settings.API_V1_PREFIX}/posts/{post_id}/comments?page={page}",
    )
    result_code = response.json()["detail"]["code"]
    result_message = response.json()["detail"]["message"]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_code == "POST_NOT_FOUND"
    assert result_message == "해당되는 글을 찾을 수 없습니다."


@pytest.mark.get_comments_of_a_user
def test_get_comments_of_a_post_if_post_exist_but_comments_not_exist(
    client: TestClient,
    db_session: Session,
    fake_post: Post,
):
    page = 1
    response = client.get(
        f"{settings.API_V1_PREFIX}/posts/{fake_post.id}/comments?page={page}",
    )
    result_code = response.json()["detail"]["code"]
    result_message = response.json()["detail"]["message"]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_code == "COMMENT_NOT_FOUND"
    assert result_message == "해당되는 댓글을 찾을 수 없습니다."


@pytest.mark.get_comments_on_a_post
def test_get_comments_on_a_post_if_post_and_comments_exist(
    client: TestClient,
    db_session: Session,
    fake_post: Post,
    fake_multi_comments: None,
):
    for page in range(4):
        response = client.get(
            f"{settings.API_V1_PREFIX}/posts/{fake_post.id}/comments?page={page}",
        )
        assert response.status_code == status.HTTP_200_OK
        if page != 3:
            assert len(response.json()) == 30
        else:
            assert len(response.json()) == 10


@pytest.mark.get_comments_of_a_user
def test_get_comments_of_a_user_if_not_registered(
    client: TestClient,
    db_session: Session,
):
    user_id = 1
    page = 1
    response = client.get(
        f"{settings.API_V1_PREFIX}/users/{user_id}/comments?page={page}",
    )
    result_code = response.json()["detail"]["code"]
    result_message = response.json()["detail"]["message"]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_code == "USER_NOT_FOUND"
    assert result_message == "해당되는 유저를 찾을 수 없습니다."


@pytest.mark.get_comments_of_a_user
def test_get_comments_of_a_user_if_comment_not_exist(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
):
    page = 1
    user = fake_user.get("user")
    response = client.get(
        f"{settings.API_V1_PREFIX}/users/{user.id}/comments?page={page}",
    )
    result_code = response.json()["detail"]["code"]
    result_message = response.json()["detail"]["message"]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_code == "COMMENT_NOT_FOUND"
    assert result_message == "해당되는 댓글을 찾을 수 없습니다."


@pytest.mark.get_comments_of_a_user
def test_get_comments_of_a_user_if_comments_exist(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
    fake_multi_comments: None,
):
    for page in range(1, 4):
        user = fake_user.get("user")
        response = client.get(
            f"{settings.API_V1_PREFIX}/users/{user.id}/comments?page={page}",
        )

        assert response.status_code == status.HTTP_200_OK
        if page != 3:
            assert len(response.json()) == 30
        else:
            assert len(response.json()) == 10


@pytest.mark.create_comment
def test_create_comment_if_not_registered(
    client: TestClient,
    db_session: Session,
    fake_post: Post,
    get_user_token_headers_and_login_data: dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data.get("headers")

    # not registered user
    user_id = 3

    # content 내용
    data_to_be_created = CommentCreate(content=random_lower_string(k=500))

    # comment 생성 및 결과
    response = client.post(
        f"{settings.API_V1_PREFIX}/users/{user_id}/posts/{fake_post.id}/comment",
        headers=headers,
        json=data_to_be_created.dict(),
    )
    result_code = response.json()["detail"]["code"]
    result_message = response.json()["detail"]["message"]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_code == "USER_NOT_FOUND"
    assert result_message == "해당되는 유저를 찾을 수 없습니다."


@pytest.mark.create_comment
def test_create_comment_if_unauthorized(
    client: TestClient,
    db_session: Session,
    fake_post: Post,
    get_user_token_headers_and_login_data: dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data.get("headers")

    # unauthorized user 생성
    password = random_lower_string(k=8)
    data_for_signup = UserCreate(
        email=random_email(),
        password=password,
        password_confirm=password,
    )
    user = user_service.create(
        db_session,
        data_for_signup.dict(),
    )
    # content 내용
    data_to_be_created = CommentCreate(content=random_lower_string(k=500))

    # content 생성 및 결과
    response = client.post(
        f"{settings.API_V1_PREFIX}/users/{user.id}/posts/{fake_post.id}/comment",
        headers=headers,
        json=data_to_be_created.dict(),
    )
    result_message = response.json().get("detail")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert result_message == "작성 권한이 없습니다."


@pytest.mark.create_comment
def test_create_comment_if_authorized(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: dict,
    fake_post: Post,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data.get("headers")
    login_data = get_user_token_headers_and_login_data.get("login_data")
    email = login_data.get("email")
    user = user_crud.get_user(db_session, email=email)

    # content 내용
    data_for_signup = CommentCreate(content=random_lower_string(k=500))

    # comment 생성 및 결과
    response = client.post(
        f"{settings.API_V1_PREFIX}/users/{user.id}/posts/{fake_post.id}/comment",
        headers=headers,
        json=data_for_signup.dict(),
    )
    content_of_created_comment = response.json()["content"]

    assert response.status_code == status.HTTP_201_CREATED
    assert content_of_created_comment == data_for_signup.content


@pytest.mark.update_comment
def test_update_comment_if_unauthorized(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: dict,
    fake_comment: Comment,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data.get("headers")

    # content 내용
    data_to_be_updated = CommentUpdate(content=random_lower_string(k=500))

    # content 내용 수정 및 결과
    response = client.put(
        f"{settings.API_V1_PREFIX}/comments/{fake_comment.id}",
        headers=headers,
        json=data_to_be_updated.dict(),
    )
    result_message = response.json().get("detail")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert result_message == "수정 권한이 없습니다."


@pytest.mark.update_comment
def test_update_comment_if_authorized(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
    fake_comment: Comment,
):
    # current_user 정보
    login_data = fake_user.get("login_data")

    # 로그인 및 JWT 생성
    login_data = {
        "email": login_data["email"],
        "password": login_data["password"],
    }
    response = client.post(f"{settings.API_V1_PREFIX}/login", json=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # content 내용
    data_to_be_updated = CommentUpdate(
        content=random_lower_string(k=500),
    )

    # content 내용 수정 및 결과
    response = client.put(
        f"{settings.API_V1_PREFIX}/comments/{fake_comment.id}",
        headers=headers,
        json=data_to_be_updated.dict(),
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("content") == data_to_be_updated.content


@pytest.mark.delete_comment
def test_delete_comment_if_unauthorized(
    client: TestClient,
    db_session: Session,
    fake_comment: Comment,
    get_user_token_headers_and_login_data: dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data.get("headers")

    # 댓글 삭제 및 결과
    response = client.delete(
        f"{settings.API_V1_PREFIX}/comments/{fake_comment.id}",
        headers=headers,
    )
    result_message = response.json().get("detail")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert result_message == "삭제 권한이 없습니다."


@pytest.mark.delete_comment
def test_delete_comment_if_authorized(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
    fake_comment: Comment,
):
    # current_user 정보
    login_data = fake_user.get("login_data")

    # 로그인 및 JWT 생성
    login_data = {
        "email": login_data["email"],
        "password": login_data["password"],
    }
    response = client.post(f"{settings.API_V1_PREFIX}/login", json=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 댓글 삭제 및 결과
    response = client.delete(
        f"{settings.API_V1_PREFIX}/comments/{fake_comment.id}",
        headers=headers,
    )
    result_status = response.json().get("status")
    result_message = response.json().get("message")

    assert response.status_code == status.HTTP_200_OK
    assert result_status == "success"
    assert result_message == "댓글이 삭제되었습니다."

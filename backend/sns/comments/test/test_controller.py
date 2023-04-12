import pytest

from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session

from sns.common.config import settings
from sns.users.test.utils import random_lower_string, random_email
from sns.users.service import get_user, create
from sns.users.schema import UserCreate
from sns.posts.model import Post
from sns.comments.model import Comment
from sns.comments.schema import CommentCreate, CommentUpdate


@pytest.mark.get_comments_on_a_post
def test_comments_on_a_post_if_post_not_exist(client: TestClient, db_session: Session):
    post_id = 1
    response = client.get(f"{settings.API_V1_PREFIX}/posts/{post_id}/comments")
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_msg == "해당 id의 포스트를 찾을 수 없습니다."


@pytest.mark.get_comments_on_a_post
def test_comments_on_a_post_if_post_exist(
    client: TestClient, db_session: Session, fake_post: Post, fake_multi_comments: None
):
    response = client.get(f"{settings.API_V1_PREFIX}/posts/{fake_post.id}/comments")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 100


@pytest.mark.get_comments_of_a_user
def test_comments_of_a_user_if_not_registered(client: TestClient, db_session: Session):
    user_id = 1
    response = client.get(f"{settings.API_V1_PREFIX}/users/{user_id}/comments")
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert result_msg == "등록된 회원이 아닙니다."


@pytest.mark.get_comments_of_a_user
def test_comments_of_a_user_if_comment_not_exist(
    client: TestClient, db_session: Session, fake_user: dict
):
    user = fake_user.get("user")
    response = client.get(f"{settings.API_V1_PREFIX}/users/{user.id}/comments")
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_msg == "작성된 댓글이 없습니다."


@pytest.mark.get_comments_of_a_user
def test_comments_of_a_user_if_comments_exist(
    client: TestClient, db_session: Session, fake_user: dict, fake_multi_comments: None
):
    user = fake_user.get("user")
    response = client.get(f"{settings.API_V1_PREFIX}/users/{user.id}/comments")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 100


@pytest.mark.create_comment
def test_create_comment_if_not_registered(
    client: TestClient,
    db_session: Session,
    fake_post: Post,
    fake_user_headers_and_info: dict,
):
    # current_user 정보
    headers = fake_user_headers_and_info.get("headers")

    # not registered user
    user_id = 2

    # content 내용
    content = CommentCreate(content=random_lower_string(k=500))
    data = jsonable_encoder(content)

    # comment 생성 및 결과
    response = client.post(
        f"{settings.API_V1_PREFIX}/users/{user_id}/posts/{fake_post.id}/comments",
        headers=headers,
        json=data,
    )
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert result_msg == "등록된 회원이 아닙니다."


@pytest.mark.create_comment
def test_create_comment_if_unauthorized(
    client: TestClient,
    db_session: Session,
    fake_post: Post,
    fake_user_headers_and_info: dict,
):
    # current_user 정보
    headers = fake_user_headers_and_info.get("headers")

    # unauthorized user 생성
    password = random_lower_string(k=8)
    user_info = UserCreate(
        email=random_email(), password=password, password_confirm=password
    )
    user = create(db_session, user_info=user_info)

    # content 내용
    content = CommentCreate(content=random_lower_string(k=500))
    data = jsonable_encoder(content)

    # content 생성 및 결과
    response = client.post(
        f"{settings.API_V1_PREFIX}/users/{user.id}/posts/{fake_post.id}/comments",
        headers=headers,
        json=data,
    )
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert result_msg == "작성할 권한이 없습니다."


@pytest.mark.create_comment
def test_create_comment_if_authorized(
    client: TestClient,
    db_session: Session,
    fake_user_headers_and_info: dict,
    fake_post: Post,
):
    # current_user 정보
    headers = fake_user_headers_and_info.get("headers")
    user_info = fake_user_headers_and_info.get("user_info")
    email = user_info.get("email")
    user = get_user(db_session, email=email)

    # content 내용
    content = CommentCreate(content=random_lower_string(k=500))
    data = jsonable_encoder(content)

    # comment 생성 및 결과
    response = client.post(
        f"{settings.API_V1_PREFIX}/users/{user.id}/posts/{fake_post.id}/comments",
        headers=headers,
        json=data,
    )
    content_of_comment_created = response.json().get("content")

    assert response.status_code == status.HTTP_201_CREATED
    assert content_of_comment_created == data.get("content")


@pytest.mark.update_comment
def test_update_comment_if_not_registered(
    client: TestClient,
    db_session: Session,
    fake_user_headers_and_info: dict,
    fake_comment: Comment,
):
    # current_user 정보
    headers = fake_user_headers_and_info.get("headers")

    # not registered user
    user_id = 2

    # content 내용
    content = CommentUpdate(
        content=random_lower_string(k=500),
    )
    data = jsonable_encoder(content)

    # content 내용 수정 및 결과
    response = client.put(
        f"{settings.API_V1_PREFIX}/users/{user_id}/comments/{fake_comment.id}",
        headers=headers,
        json=data,
    )
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert result_msg == "등록된 회원이 아닙니다."


@pytest.mark.update_comment
def test_update_comment_if_unauthorized(
    client: TestClient,
    db_session: Session,
    fake_comment: Comment,
    fake_user_headers_and_info: dict,
):
    # current_user 정보
    headers = fake_user_headers_and_info.get("headers")
    user_info = fake_user_headers_and_info.get("user_info")

    # unauthorized user 생성
    password = random_lower_string(k=8)
    user_info = UserCreate(
        email=random_email(), password=password, password_confirm=password
    )
    user = create(db_session, user_info=user_info)

    # content 내용
    content = CommentUpdate(
        content=random_lower_string(k=500),
    )
    data = jsonable_encoder(content)

    # content 내용 수정 및 결과
    response = client.put(
        f"{settings.API_V1_PREFIX}/users/{user.id}/comments/{fake_comment.id}",
        headers=headers,
        json=data,
    )
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert result_msg == "수정할 권한이 없습니다."


@pytest.mark.update_comment
def test_update_comment_if_authorized(
    client: TestClient,
    db_session: Session,
    fake_comment: Comment,
    fake_user_headers_and_info: dict,
):
    # current_user 정보
    headers = fake_user_headers_and_info.get("headers")
    user_info = fake_user_headers_and_info.get("user_info")
    email = user_info.get("email")
    user = get_user(db_session, email=email)

    # content 내용
    content = CommentUpdate(
        content=random_lower_string(k=500),
    )
    data = jsonable_encoder(content)

    # content 내용 수정 및 결과
    response = client.put(
        f"{settings.API_V1_PREFIX}/users/{user.id}/comments/{fake_comment.id}",
        headers=headers,
        json=data,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("content") == data.get("content")


@pytest.mark.delete_comment
def test_delete_comment_if_not_registered(
    client: TestClient,
    db_session: Session,
    fake_comment: Comment,
    fake_user_headers_and_info: dict,
):
    # current_user 정보
    headers = fake_user_headers_and_info.get("headers")

    # not registered user
    user_id = 2

    # 댓글 삭제 및 결과
    response = client.delete(
        f"{settings.API_V1_PREFIX}/users/{user_id}/comments/{fake_comment.id}",
        headers=headers,
    )
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert result_msg == "등록된 회원이 아닙니다."


@pytest.mark.delete_comment
def test_delete_comment_if_not_unauthorized(
    client: TestClient,
    db_session: Session,
    fake_comment: Comment,
    fake_user_headers_and_info: dict,
):
    # current_user 정보
    headers = fake_user_headers_and_info.get("headers")

    # unauthorized user 생성
    password = random_lower_string(k=8)
    user_info = UserCreate(
        email=random_email(), password=password, password_confirm=password
    )
    user = create(db_session, user_info=user_info)

    # 댓글 삭제 및 결과
    response = client.delete(
        f"{settings.API_V1_PREFIX}/users/{user.id}/comments/{fake_comment.id}",
        headers=headers,
    )
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert result_msg == "삭제할 권한이 없습니다."


@pytest.mark.delete_comment
def test_delete_comment_if_authorized(
    client: TestClient,
    db_session: Session,
    fake_comment: Comment,
    fake_user_headers_and_info: dict,
):
    # current_user 정보
    headers = fake_user_headers_and_info.get("headers")
    user_info = fake_user_headers_and_info.get("user_info")
    email = user_info.get("email")
    user = get_user(db_session, email=email)

    # 댓글 삭제 및 결과
    response = client.delete(
        f"{settings.API_V1_PREFIX}/users/{user.id}/comments/{fake_comment.id}",
        headers=headers,
    )
    result_status = response.json().get("status")
    result_msg = response.json().get("msg")

    assert response.status_code == status.HTTP_200_OK
    assert result_status == "success"
    assert result_msg == "댓글이 삭제되었습니다."

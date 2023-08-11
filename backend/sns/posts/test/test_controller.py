from typing import Dict
from random import randint

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from fastapi import status
import pytest

from sns.common.config import settings
from sns.users.test.utils import random_lower_string
from sns.users.service import user_service
from sns.posts.schema import PostCreate, PostUpdate
from sns.posts.service import post_service
from sns.posts import model


@pytest.mark.read_post
def test_read_post_existed(
    client: TestClient,
    fake_multi_posts: None,
):
    total_post_count = 100
    for post_id in range(1, total_post_count + 1):
        response = client.get(f"{settings.API_V1_PREFIX}/posts/{post_id}")
        post = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert response is not None
        assert post["id"] == post_id


@pytest.mark.read_post
def test_read_post_not_existed(
    client: TestClient,
    fake_post: model.Post,
):
    post_id = randint(fake_post.id + 1, 100)
    response = client.get(f"{settings.API_V1_PREFIX}/posts/{post_id}")
    result_msg = response.json()["detail"]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_msg == "해당 id의 글을 찾을 수 없습니다."


@pytest.mark.read_posts
def test_read_posts_if_not_registered(
    client: TestClient,
):
    # 가짜 유저 id
    user_id = 1

    # page number
    page = 1

    # 글 조회 및 결과
    response = client.get(f"{settings.API_V1_PREFIX}/users/{user_id}/posts?page={page}")
    result_msg = response.json()["detail"]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_msg == "해당되는 유저를 찾을 수 없습니다."


@pytest.mark.read_posts
def test_read_posts_if_post_not_exist(
    client: TestClient,
    fake_user: Dict,
):
    # 유저 정보
    user = fake_user["user"]

    # page number
    page = 1

    # 글 조회 및 결과
    response = client.get(f"{settings.API_V1_PREFIX}/users/{user.id}/posts?page={page}")
    result_msg = response.json()["detail"]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_msg == "작성된 글이 없습니다."


@pytest.mark.read_posts
def test_read_posts_if_post_exist(
    client: TestClient,
    fake_user: Dict,
    fake_multi_posts: None,
):
    # 유저 정보
    user = fake_user["user"]

    for page in range(20):
        # 글 조회 및 결과
        response = client.get(
            f"{settings.API_V1_PREFIX}/users/{user.id}/posts?page={page}",
        )
        result = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert len(result) == 5


@pytest.mark.create_post
def test_create_post_if_user_not_registered(
    client: TestClient,
    get_user_token_headers_and_login_data: Dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]

    # 생성할 글 content 정보
    content = PostCreate(content=random_lower_string(k=1000))

    # 등록되지 않은 유저 id
    not_registered_user_id = 2

    # 글 생성 및 결과
    response = client.post(
        f"{settings.API_V1_PREFIX}/users/{not_registered_user_id}/posts",
        headers=headers,
        json=content.dict(),
    )
    result_msg = response.json()["detail"]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_msg == "해당되는 유저를 찾을 수 없습니다."


@pytest.mark.create_post
def test_create_post_if_unauthorized(
    client: TestClient,
    fake_user: Dict,
    get_user_token_headers_and_login_data: Dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]

    # 생성할 글 content 정보
    content = PostCreate(content=random_lower_string(k=1000))

    # 인가받지 않은 user 정보
    unauthorized_user = fake_user["user"]

    # 글 생성 및 결과
    response = client.post(
        f"{settings.API_V1_PREFIX}/users/{unauthorized_user.id}/posts",
        headers=headers,
        json=content.dict(),
    )
    result_msg = response.json()["detail"]

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert result_msg == "작성할 권한이 없습니다."


@pytest.mark.create_post
def test_create_post_if_authorized(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: Dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]
    login_data = get_user_token_headers_and_login_data["login_data"]
    authorized_user = user_service.get_user(db_session, email=login_data["email"])

    # 생성할 글 content 정보
    content = PostCreate(content=random_lower_string(k=1000))

    # 글 생성 및 결과
    response = client.post(
        f"{settings.API_V1_PREFIX}/users/{authorized_user.id}/posts",
        headers=headers,
        json=content.dict(),
    )
    created_post_id = response.json()["id"]
    post = post_service.get_post_and_check_none(db_session, post_id=created_post_id)

    assert response.status_code == status.HTTP_201_CREATED
    assert post is not None


@pytest.mark.update_post
def test_update_post_if_user_not_registered(
    client: TestClient,
    get_user_token_headers_and_login_data: Dict,
    fake_post: model.Post,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]

    # 변경할 글 content 정보
    content = PostUpdate(content=random_lower_string(k=1000))

    # 등록되지 않은 유저 id
    not_registered_user_id = 3

    # 글 수정 및 결과
    response = client.patch(
        f"{settings.API_V1_PREFIX}/users/{not_registered_user_id}/posts/{fake_post.id}",
        headers=headers,
        json=content.dict(),
    )
    result_msg = response.json()["detail"]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_msg == "해당되는 유저를 찾을 수 없습니다."


@pytest.mark.update_post
def test_update_post_if_try_to_update_not_mine(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: Dict,
    fake_post: model.Post,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]
    login_data = get_user_token_headers_and_login_data["login_data"]
    authorized_user = user_service.get_user(db_session, email=login_data["email"])

    # 변경할 content 정보
    content = PostUpdate(content=random_lower_string(k=1000))

    # 글 수정 및 결과 - 현재 로그인된 유저가 자신이 작성한 글 이외의 글을 시도할 경우
    response = client.patch(
        f"{settings.API_V1_PREFIX}/users/{authorized_user.id}/posts/{fake_post.id}",
        headers=headers,
        json=content.dict(),
    )
    result_msg = response.json()["detail"]

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert result_msg == "수정할 권한이 없습니다."


@pytest.mark.update_post
def test_update_post_if_user_id_is_not_same_as_user_logged_in(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: Dict,
    fake_post_by_user_logged_in: model.Post,
    fake_user: dict,
):
    # 현재 로그인 상태가 아닌 유저
    user_id_not_logged_in = fake_user["user"].id

    # 로그인 상태의 유저
    headers = get_user_token_headers_and_login_data["headers"]

    # 로그인한 유저가 작성한 post id
    post_id = fake_post_by_user_logged_in.id

    # 변경할 content 정보
    content = PostUpdate(content=random_lower_string(k=1000))

    response = client.patch(
        f"{settings.API_V1_PREFIX}/users/{user_id_not_logged_in}/posts/{post_id}",
        headers=headers,
        json=content.dict(),
    )
    result_msg = response.json()["detail"]

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert result_msg == "수정할 권한이 없습니다."


@pytest.mark.update_post
def test_update_post_if_post_not_exist(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: Dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]
    login_data = get_user_token_headers_and_login_data["login_data"]
    authorized_user = user_service.get_user(db_session, email=login_data["email"])

    # 변경할 content 정보
    content = PostUpdate(content=random_lower_string(k=1000))

    # 존재하지 않는 post id
    post_id = 1

    # 글 수정 및 결과
    response = client.patch(
        f"{settings.API_V1_PREFIX}/users/{authorized_user.id}/posts/{post_id}",
        headers=headers,
        json=content.dict(),
    )
    result_msg = response.json()["detail"]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_msg == "해당 id의 글을 찾을 수 없습니다."


@pytest.mark.update_post
def test_update_post_only_one_if_authorized(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: Dict,
    fake_post_by_user_logged_in: model.Post,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]
    login_data = get_user_token_headers_and_login_data["login_data"]
    authorized_user = user_service.get_user(db_session, email=login_data["email"])

    # 로그인한 유저가 작성한 post id
    post_id = fake_post_by_user_logged_in.id

    # 변경할 content 정보
    content = PostUpdate(content=random_lower_string(k=1000))

    # 글 수정 및 결과
    response = client.patch(
        f"{settings.API_V1_PREFIX}/users/{authorized_user.id}/posts/{post_id}",
        headers=headers,
        json=content.dict(),
    )
    content_updated = response.json()["content"]

    assert response.status_code == status.HTTP_200_OK
    assert content_updated == content.dict()["content"]


@pytest.mark.update_post
def test_update_post_multi_posts_if_authorized(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: Dict,
    fake_multi_post_by_user_logged_in: None,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]
    login_data = get_user_token_headers_and_login_data["login_data"]
    authorized_user = user_service.get_user(db_session, email=login_data["email"])

    for post_id in range(1, 101):
        # 변경할 content 정보
        content = PostUpdate(content=random_lower_string(k=1000))

        # 글 수정 및 결과
        response = client.patch(
            f"{settings.API_V1_PREFIX}/users/{authorized_user.id}/posts/{post_id}",
            headers=headers,
            json=content.dict(),
        )
        result_content = response.json()["content"]
        result_id = response.json()["id"]

        assert response.status_code == status.HTTP_200_OK
        assert response is not None
        assert result_content == content.dict()["content"]
        assert result_id == post_id


@pytest.mark.delete_post
def test_delete_post_if_authorized(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: Dict,
    fake_post_by_user_logged_in: model.Post,
):
    # user 및 post 정보
    headers = get_user_token_headers_and_login_data["headers"]
    login_data = get_user_token_headers_and_login_data["login_data"]
    user = user_service.get_user(db_session, email=login_data["email"])
    post_id = fake_post_by_user_logged_in.id

    # 글 삭제 및 결과
    response = client.delete(
        f"{settings.API_V1_PREFIX}/users/{user.id}/posts/{post_id}",
        headers=headers,
    )
    result_status_text = response.json()["status"]
    result_msg = response.json()["msg"]

    assert response.status_code == status.HTTP_200_OK
    assert result_status_text == "success"
    assert result_msg == "글이 삭제되었습니다."

    # 결과 확인
    with pytest.raises(HTTPException):
        post_service.get_post_and_check_none(db_session, post_id=post_id)


@pytest.mark.delete_post
def test_delete_post_if_not_authorized(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: Dict,
    fake_post: model.Post,
):
    # 로그인 상태의 유저
    headers = get_user_token_headers_and_login_data["headers"]
    login_data = get_user_token_headers_and_login_data["login_data"]
    user = user_service.get_user(db_session, email=login_data["email"])

    # 삭제 대상 post의 id
    post_id = fake_post.id

    # 글 삭제 및 결과
    response = client.delete(
        f"{settings.API_V1_PREFIX}/users/{user.id}/posts/{post_id}",
        headers=headers,
    )
    result_msg = response.json()["detail"]

    # 결과 확인
    post = post_service.get_post_and_check_none(db_session, post_id=post_id)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert result_msg == "삭제할 권한이 없습니다."
    assert post is not None


@pytest.mark.read_likers
def test_read_likers(client: TestClient, db_session: Session, fake_postlike: None):
    for post_id in range(1, 101):
        if post_id <= 50:
            response = client.get(f"{settings.API_V1_PREFIX}/posts/{post_id}/likers")
            result = response.json()

            assert response.status_code == status.HTTP_200_OK
            assert len(result) == 2
        else:
            response = client.get(f"{settings.API_V1_PREFIX}/posts/{post_id}/likers")
            result = response.json()

            assert response.status_code == status.HTTP_200_OK
            assert len(result) == 1


@pytest.mark.read_likees
def test_read_likees_if_likees_not_exist(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: dict,
):
    # current user 정보
    headers = get_user_token_headers_and_login_data.get("headers")

    # likees 조회 및 결과
    response = client.get(f"{settings.API_V1_PREFIX}/posts/likees", headers=headers)
    result_msg = response.json()["detail"]

    assert result_msg == "해당 유저가 좋아요를 한 글이 없습니다."


@pytest.mark.read_likees
def test_read_likees_if_likees_exist(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
    fake_postlike: None,
):
    # login 정보
    user = fake_user.get("user")
    login_data = fake_user.get("login_data")

    # verified 업데이트
    user_service.update(
        db_session,
        user,
        {"verified": True},
    )

    # token 발행
    response = client.post(
        f"{settings.API_V1_PREFIX}/login",
        json=login_data,
    )
    token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # likees 조회 및 결과
    response = client.get(f"{settings.API_V1_PREFIX}/posts/likees", headers=headers)
    result = response.json()

    assert len(result) == 50


@pytest.mark.like_post
def test_like_post(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: dict,
    fake_multi_posts: None,
):
    headers = get_user_token_headers_and_login_data.get("headers")

    for post_id in range(1, 101):
        response = client.post(
            f"{settings.API_V1_PREFIX}/posts/{post_id}/like",
            headers=headers,
        )
        result = response.json()
        result_status_text = result.get("status")
        result_msg = result.get("msg")

        assert response.status_code == status.HTTP_200_OK
        assert result_status_text == "success"
        assert result_msg == "post 좋아요가 완료되었습니다."


@pytest.mark.unlike_post
def test_unlike_post(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: dict,
    fake_multi_posts: None,
):
    headers = get_user_token_headers_and_login_data.get("headers")

    for post_id in range(1, 101):
        response = client.post(
            f"{settings.API_V1_PREFIX}/posts/{post_id}/like",
            headers=headers,
        )

    for post_id in range(1, 101):
        response = client.post(
            f"{settings.API_V1_PREFIX}/posts/{post_id}/unlike",
            headers=headers,
        )
        result_status_text = response.json().get("status")
        result_msg = response.json().get("msg")

        assert response.status_code == status.HTTP_200_OK
        assert result_status_text == "success"
        assert result_msg == "post 좋아요가 취소되었습니다"

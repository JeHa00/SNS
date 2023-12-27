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
from sns.users.repositories.db import user_crud
from sns.posts.schema import PostCreate, PostUpdate
from sns.posts.service import post_service
from sns.posts.model import Post


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
    fake_post: Post,
):
    post_id = randint(fake_post.id + 1, 100)
    response = client.get(f"{settings.API_V1_PREFIX}/posts/{post_id}")
    result_code = response.json()["detail"]["code"]
    result_message = response.json()["detail"]["message"]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_code == "POST_NOT_FOUND"
    assert result_message == "해당되는 글을 찾을 수 없습니다."


@pytest.mark.read_posts
def test_read_posts_if_posts_not_exist(client: TestClient):
    # page number
    page = 0

    # 글 조회 및 결과
    response = client.get(f"{settings.API_V1_PREFIX}/posts?page={page}")

    # posts가 존재하지 않으면 빈 리스트를 반환
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.read_posts
def test_read_posts_if_posts_exist(
    client: TestClient,
    fake_multi_posts: None,
):
    for page in range(20):
        # 글 조회 및 결과
        response = client.get(
            f"{settings.API_V1_PREFIX}/posts?page={page}",
        )
        result = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert len(result) == 5


@pytest.mark.read_user_posts
def test_read_posts_of_a_user_if_not_registered(
    client: TestClient,
):
    # 가짜 유저 id
    user_id = 1

    # page number
    page = 0

    # 글 조회 및 결과
    response = client.get(f"{settings.API_V1_PREFIX}/users/{user_id}/posts?page={page}")
    result_code = response.json()["detail"]["code"]
    result_message = response.json()["detail"]["message"]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_code == "USER_NOT_FOUND"
    assert result_message == "해당되는 유저를 찾을 수 없습니다."


@pytest.mark.read_user_posts
def test_read_posts_of_a_user_if_post_not_exist(
    client: TestClient,
    fake_user: Dict,
):
    # 유저 정보
    user = fake_user["user"]

    # page number
    page = 0

    # 글 조회 및 결과
    response = client.get(f"{settings.API_V1_PREFIX}/users/{user.id}/posts?page={page}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.read_user_posts
def test_read_posts_of_a_user_if_post_exist(
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


@pytest.mark.read_posts_of_followers
def test_read_posts_of_followers_if_followers_not_exist(
    client: TestClient,
    get_user_token_headers_and_login_data: dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]

    page = 0

    # 팔로워들의 글 정보 요청
    response = client.get(
        f"{settings.API_V1_PREFIX}/posts/followers?page={page}",
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.read_posts_of_followers
def test_read_posts_of_followers_if_success_and_posts_not_exist(
    client: TestClient,
    get_user_token_headers_and_login_data: dict,
    fake_user: dict,
    fake_multi_posts,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]

    follower_id = fake_user.get("user").id

    # follow 요청
    response = client.post(
        f"{settings.API_V1_PREFIX}/users/{follower_id}/follow",
        headers=headers,
    )

    for page in range(21):
        # 팔로워들의 글 정보 요청
        response = client.get(
            f"{settings.API_V1_PREFIX}/posts/followers?page={page}",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK

        if page == 20:
            assert response.json() == []
        else:
            assert len(response.json()) == 5


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
    result_message = response.json()["detail"]

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert result_message == "작성 권한이 없습니다."


@pytest.mark.create_post
def test_create_post_if_authorized(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: Dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]
    login_data = get_user_token_headers_and_login_data["login_data"]
    authorized_user = user_crud.get_user(db_session, email=login_data["email"])

    # 생성할 글 content 정보
    content = PostCreate(content=random_lower_string(k=1000))

    # 글 생성 및 결과
    response = client.post(
        f"{settings.API_V1_PREFIX}/users/{authorized_user.id}/posts",
        headers=headers,
        json=content.dict(),
    )
    created_post_id = response.json()["id"]
    post = post_service.get_post_and_handle_none(db_session, post_id=created_post_id)

    assert response.status_code == status.HTTP_201_CREATED
    assert post is not None


@pytest.mark.update_post
def test_update_post_if_try_to_update_not_mine(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: Dict,
    fake_post: Post,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]
    login_data = get_user_token_headers_and_login_data["login_data"]
    authorized_user = user_crud.get_user(db_session, email=login_data["email"])

    # 변경할 content 정보
    content = PostUpdate(content=random_lower_string(k=1000))

    # 글 수정 및 결과 - 현재 로그인된 유저가 자신이 작성한 글 이외의 글을 시도할 경우
    response = client.patch(
        f"{settings.API_V1_PREFIX}/users/{authorized_user.id}/posts/{fake_post.id}",
        headers=headers,
        json=content.dict(),
    )
    result_message = response.json()["detail"]

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert result_message == "수정 권한이 없습니다."


@pytest.mark.update_post
def test_update_post_if_post_not_exist(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: Dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]
    login_data = get_user_token_headers_and_login_data["login_data"]
    authorized_user = user_crud.get_user(db_session, email=login_data["email"])

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
    result_code = response.json()["detail"]["code"]
    result_message = response.json()["detail"]["message"]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_code == "POST_NOT_FOUND"
    assert result_message == "해당되는 글을 찾을 수 없습니다."


@pytest.mark.update_post
def test_update_post_only_one_if_authorized(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: Dict,
    fake_post_by_user_logged_in: Post,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]
    login_data = get_user_token_headers_and_login_data["login_data"]
    authorized_user = user_crud.get_user(db_session, email=login_data["email"])

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
    authorized_user = user_crud.get_user(db_session, email=login_data["email"])

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
    fake_post_by_user_logged_in: Post,
):
    # user 및 post 정보
    headers = get_user_token_headers_and_login_data["headers"]
    login_data = get_user_token_headers_and_login_data["login_data"]
    user = user_crud.get_user(db_session, email=login_data["email"])
    post_id = fake_post_by_user_logged_in.id

    # 글 삭제 및 결과
    response = client.delete(
        f"{settings.API_V1_PREFIX}/users/{user.id}/posts/{post_id}",
        headers=headers,
    )
    result_status_text = response.json()["status"]
    result_message = response.json()["message"]

    assert response.status_code == status.HTTP_200_OK
    assert result_status_text == "success"
    assert result_message == "글이 삭제되었습니다."

    # 결과 확인
    with pytest.raises(HTTPException):
        post_service.get_post_and_handle_none(db_session, post_id=post_id)


@pytest.mark.delete_post
def test_delete_post_if_unauthorized(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: Dict,
    fake_post: Post,
):
    # 로그인 상태의 유저
    headers = get_user_token_headers_and_login_data["headers"]
    login_data = get_user_token_headers_and_login_data["login_data"]
    user = user_crud.get_user(db_session, email=login_data["email"])

    # 삭제 대상 post의 id
    post_id = fake_post.id

    # 글 삭제 및 결과
    response = client.delete(
        f"{settings.API_V1_PREFIX}/users/{user.id}/posts/{post_id}",
        headers=headers,
    )
    result_message = response.json()["detail"]

    # 결과 확인
    post = post_service.get_post_and_handle_none(db_session, post_id=post_id)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert result_message == "삭제 권한이 없습니다."
    assert post is not None


@pytest.mark.read_users_who_like
def test_read_users_who_like_if_user_and_post_exist(
    client: TestClient,
    db_session: Session,
    fake_postlike: None,
):
    page = 0

    for post_id in range(1, 101):
        response = client.get(
            f"{settings.API_V1_PREFIX}/posts/{post_id}/users_who_like?page={page}",
        )

        result = response.json()

        assert response.status_code == status.HTTP_200_OK

        if post_id <= 50:
            assert len(result) == 2
        else:
            assert len(result) == 1


@pytest.mark.read_users_who_like
def test_read_users_who_like_if_post_not_exist(
    client: TestClient,
    db_session: Session,
):
    not_exist_post_id = 1

    response = client.get(
        f"{settings.API_V1_PREFIX}/posts/{not_exist_post_id}/users_who_like?page={0}",
    )
    result_code = response.json()["detail"]["code"]
    result_message = response.json()["detail"]["message"]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_code == "POST_NOT_FOUND"
    assert result_message == "해당되는 글을 찾을 수 없습니다."


@pytest.mark.read_users_who_like
def test_read_users_who_like_if_postlike_not_exist(
    client: TestClient,
    db_session: Session,
    fake_post: Post,
):
    response = client.get(
        f"{settings.API_V1_PREFIX}/posts/{fake_post.id}/users_who_like?page={0}",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.read_liked_posts
def test_read_liked_posts_if_likees_not_exist(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: dict,
):
    # current user 정보
    headers = get_user_token_headers_and_login_data.get("headers")

    # liked_posts 조회 및 결과
    response = client.get(
        f"{settings.API_V1_PREFIX}/posts/liked_posts?page={0}",
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.read_liked_posts
def test_read_liked_posts_if_likees_exist(
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
    for page in range(11):
        response = client.get(
            f"{settings.API_V1_PREFIX}/posts/liked_posts?page={page}",
            headers=headers,
        )
        result = response.json()

        if page == 10:
            assert result == []
        else:
            assert len(result) == 5


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
        result_message = result.get("message")

        assert response.status_code == status.HTTP_200_OK
        assert result_status_text == "success"
        assert result_message == "post 좋아요가 완료되었습니다."


@pytest.mark.like_post
def test_like_post_if_post_not_exist(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: dict,
):
    headers = get_user_token_headers_and_login_data.get("headers")

    post_id = 1

    response = client.post(
        f"{settings.API_V1_PREFIX}/posts/{post_id}/like",
        headers=headers,
    )
    result_code = response.json()["detail"]["code"]
    result_message = response.json()["detail"]["message"]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_code == "POST_NOT_FOUND"
    assert result_message == "해당되는 글을 찾을 수 없습니다."


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
        result_message = response.json().get("message")

        assert response.status_code == status.HTTP_200_OK
        assert result_status_text == "success"
        assert result_message == "post 좋아요가 취소되었습니다"


@pytest.mark.unlike_post
def test_unlike_post_if_post_not_exist(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: dict,
):
    headers = get_user_token_headers_and_login_data.get("headers")

    post_id = 1

    response = client.post(
        f"{settings.API_V1_PREFIX}/posts/{post_id}/unlike",
        headers=headers,
    )
    result = response.json()["detail"]
    result_status_text = result.get("code")
    result_message = result.get("message")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_status_text == "POST_NOT_FOUND"
    assert result_message == "주어진 정보에 일치하는 글을 찾을 수 없습니다."


@pytest.mark.unlike_post
def test_unlike_post_if_postlike_not_exist(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: dict,
    fake_post: Post,
):
    headers = get_user_token_headers_and_login_data.get("headers")

    response = client.post(
        f"{settings.API_V1_PREFIX}/posts/{fake_post.id}/unlike",
        headers=headers,
    )
    result = response.json()["detail"]
    result_status_text = result.get("code")
    result_message = result.get("message")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_status_text == "POST_LIKE_NOT_FOUND"
    assert result_message == "해당 정보에 일치하는 좋아요 정보를 찾을 수 없습니다."

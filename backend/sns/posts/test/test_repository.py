from typing import List

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from sns.users.test.utils import random_lower_string
from sns.users.service import user_service
from sns.users.model import User
from sns.posts.repository import post_crud
from sns.posts.model import Post, PostLike
from sns.posts import schema


def test_create(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
):
    writer = fake_user.get("user")
    post_data = schema.PostCreate(content=random_lower_string(k=1000))
    post = post_crud.create(
        db_session,
        writer.id,
        **post_data.dict(),
    )

    assert post
    assert hasattr(post, "id")
    assert post.id == 1
    assert hasattr(post, "content")
    assert hasattr(post, "writer_id")
    assert post.writer_id == writer.id
    assert hasattr(post, "writer")
    assert post.writer == writer
    assert hasattr(post, "created_at")
    assert hasattr(post, "updated_at")


def test_get_post(
    client: TestClient,
    db_session: Session,
    fake_post: Post,
    fake_user: dict,
):
    writer = fake_user.get("user")
    post = post_crud.get_post(
        db_session,
        fake_post.id,
    )

    assert post
    assert hasattr(post, "id")
    assert post.id == 1
    assert hasattr(post, "content")
    assert hasattr(post, "writer_id")
    assert post.writer_id == writer.id
    assert hasattr(post, "writer")
    assert post.writer == writer
    assert hasattr(post, "created_at")
    assert hasattr(post, "updated_at")


def test_get_multi_posts(
    client: TestClient,
    db_session: Session,
    fake_multi_posts: List[Post],
    fake_user: dict,
):
    writer = fake_user.get("user")
    for page in range(20):
        posts = post_crud.get_multi_posts(
            db_session,
            writer.id,
            skip=page * 5,
        )

        assert posts
        assert len(posts) == 5  # query에 사용하는 limit의 기본값이 5

        for post in posts:
            assert hasattr(post, "id")
            assert hasattr(post, "content")
            assert hasattr(post, "writer_id")
            assert post.writer_id == writer.id
            assert hasattr(post, "writer")
            assert post.writer == writer
            assert hasattr(post, "created_at")
            assert hasattr(post, "updated_at")


def test_update_only_one_by_model_object(
    client: TestClient,
    db_session: Session,
    fake_post: Post,
):
    content_before_update = fake_post.content  # 업데이트 전 내용
    data_to_be_updated = schema.PostUpdate(content="Hello World!")  # 업데이트할 내용

    # 업데이트된 포스트
    post = post_crud.update(
        db_session,
        fake_post,
        **data_to_be_updated.dict(),
    )
    content_after_update = post.content  # 업데이트된 내용

    assert content_after_update == "Hello World!"
    assert content_before_update != content_after_update


def test_update_multi_posts_by_model_object(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
    fake_multi_posts: List[Post],
):
    # 생성한 post 목록들
    user = fake_user.get("user")
    posts = post_crud.get_multi_posts(
        db_session,
        user.id,
    )

    data_to_be_updated = schema.PostUpdate(content="Hello World!")  # 업데이트할 내용

    for post in posts:
        post_crud.update(
            db_session,
            post,
            **data_to_be_updated.dict(),
        )
        assert post.content == "Hello World!"


def test_delete_only_one_by_model_object(
    client: TestClient,
    db_session: Session,
    fake_post: Post,
):
    post_id = fake_post.id
    post_crud.remove(
        db_session,
        fake_post,
    )
    post = post_crud.get_post(
        db_session,
        post_id,
    )

    assert post is None


def test_delete_multi_posts_by_model_object(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
    fake_multi_posts: List[Post],
):
    # 생성한 post 목록들
    user = fake_user.get("user")

    # fake_post로 생성한 수가 100개
    posts = post_crud.get_multi_posts(
        db_session,
        user.id,
        limit=100,
    )

    for post in posts:
        post_crud.remove(
            db_session,
            post,
        )

    posts = post_crud.get_multi_posts(
        db_session,
        user.id,
    )

    assert len(posts) == 0


def test_delete_user_having_multi_posts(
    client: TestClient,
    db_session: Session,
    fake_user,
    fake_multi_posts: None,
):
    user = fake_user.get("user")
    user_service.remove(
        db_session,
        user,
    )
    posts = post_crud.get_multi_posts(
        db_session,
        user.id,
    )

    assert len(posts) == 0


def test_like_if_post_like_not_exist(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
    fake_multi_posts: None,
):
    user = fake_user.get("user")

    for post_id in range(1, 101):
        like_data = {
            "who_like_id": user.id,
            "like_target_id": post_id,
        }
        post_crud.like(
            db_session,
            None,
            **like_data,
        )

    posts = post_crud.get_like_targets(
        db_session,
        user.id,
    )

    assert len(posts) == 100


def test_get_users_who_like(
    client: TestClient,
    db_session: Session,
    fake_postlike: None,
):
    users_about_post_one = post_crud.get_users_who_like(db_session, 1)
    users_about_post_second = post_crud.get_users_who_like(db_session, 51)

    assert users_about_post_one is not None
    assert len(users_about_post_one) == 2
    assert users_about_post_second is not None
    assert len(users_about_post_second) == 1


def test_get_like_targets(
    client: TestClient,
    db_session: Session,
    fake_postlike: None,
):
    posts_on_user_one = post_crud.get_like_targets(db_session, 1)
    posts_on_user_two = post_crud.get_like_targets(db_session, 2)

    assert posts_on_user_one is not None
    assert len(posts_on_user_one) == 50
    assert posts_on_user_two is not None
    assert len(posts_on_user_two) == 100


def test_unlike(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
    fake_postlike: None,
):
    user = fake_user.get("user")

    for post_id in range(1, 51):
        post_like_data = {
            "who_like_id": user.id,  # id = 1
            "like_target_id": post_id,
        }
        post_like_object: PostLike = post_crud.get_like(db_session, post_like_data)
        post_crud.unlike(
            db_session,
            post_like_object,
        )

        who_like: List[PostLike] = post_crud.get_users_who_like(
            db_session,
            post_id,
        )

        # fake_user와 fake_postlike에서 another user를 생성하여 총 user id가 2까지 존재하는 상황
        assert len(who_like) == 1  # who_like_id=2 인 유저 정보만 조회

    for post_id in range(1, 101):
        post_like_data = {
            "who_like_id": 2,
            "like_target_id": post_id,
        }
        post_like_object: PostLike = post_crud.get_like(
            db_session,
            post_like_data,
        )
        post_crud.unlike(
            db_session,
            post_like_object,
        )

        who_like: List[PostLike] = post_crud.get_users_who_like(
            db_session,
            post_id,
        )

        assert len(who_like) == 0


def test_like_if_post_like_already_exist(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
    fake_postlike: None,
):
    user = fake_user.get("user")

    for post_id in range(1, 51):
        post_like_data = {
            "who_like_id": user.id,  # id = 1
            "like_target_id": post_id,
        }
        post_like_object: PostLike = post_crud.get_like(db_session, post_like_data)

        # unlike 실행하기
        post_crud.unlike(
            db_session,
            post_like_object,
        )

        who_like: List[PostLike] = post_crud.get_users_who_like(
            db_session,
            post_id,
        )

        # fake_user와 fake_postlike에서 another user를 생성하여 총 user id가 2까지 존재하는 상황
        assert len(who_like) == 1  # who_like_id=2 인 유저 정보만 조회

        # 다시 like 실행하기
        post_crud.like(db_session, post_like_object)

        who_like: List[User] = post_crud.get_users_who_like(
            db_session,
            post_id,
        )

        assert len(who_like) == 2

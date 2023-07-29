from typing import List

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from sns.users.test.utils import random_lower_string
from sns.users.service import user_service
from sns.posts.repository import post_crud
from sns.posts.model import Post
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
    posts = post_crud.get_multi_posts(
        db_session,
        writer.id,
    )

    assert posts
    assert len(posts) == 10  # query에 사용하는 limit의 기본값이 10
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


# FIXME: int를 사용하여 post를 조회 후 업데이트를 여러 post에 시도 시 문제가 없지만, model object를 사용하면 문제가 발생된다.
# FIXME: post model 객체는 넘어가지만, update 내부 jsonable_encoder가 반환 시 첫 번째 model object만 반환한다.
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


def test_like(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
    fake_multi_posts: None,
):
    user = fake_user.get("user")

    for post_id in range(1, 101):
        like_data = schema.PostLike(
            who_like_id=user.id,
            like_target_id=post_id,
        )
        post_crud.like(
            db_session,
            like_data.dict(),
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
        unlike_data = schema.PostUnlike(
            who_like_id=user.id,
            like_target_id=post_id,
        )
        post_crud.unlike(
            db_session,
            unlike_data.dict(),
        )

        who_like = post_crud.get_users_who_like(
            db_session,
            post_id,
        )
        assert len(who_like) == 1  # who_like_id=2 인 유저 정보만 조회

    for post_id in range(1, 101):
        unlike_data = schema.PostUnlike(
            who_like_id=2,
            like_target_id=post_id,
        )
        post_crud.unlike(
            db_session,
            unlike_data.dict(),
        )

        who_like = post_crud.get_users_who_like(
            db_session,
            post_id,
        )

        assert len(who_like) == 0

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from sns.users.repositories.db import user_crud
from sns.posts.repository import post_crud
from sns.notifications.repository import notification_crud
from sns.notifications.enums import NotificationType


def test_create_and_get_notification_on_follow_then_mark_as_read(
    client: TestClient,
    db_session: Session,
    fake_follow: None,
):
    total_user_count = 10
    for follower_id in range(1, total_user_count + 1):
        for following_id in range(1, total_user_count + 1):
            if follower_id == following_id:
                continue

            selected_follow = user_crud.get_follow(
                db_session,
                follower_id=follower_id,
                following_id=following_id,
            )

            new_notification_about_follow = (
                notification_crud.create_notification_on_follow(
                    db_session,
                    selected_follow.id,
                    selected_follow.follower_id,
                )
            )

            assert hasattr(new_notification_about_follow, "id")
            assert hasattr(new_notification_about_follow, "created_at")
            assert hasattr(new_notification_about_follow, "updated_at")
            assert hasattr(new_notification_about_follow, "read")
            assert hasattr(new_notification_about_follow, "follow_id")
            assert hasattr(new_notification_about_follow, "post_like_id")
            assert hasattr(new_notification_about_follow, "notified_user_id")
            assert hasattr(new_notification_about_follow, NotificationType.follow)
            assert new_notification_about_follow.read is False
            assert new_notification_about_follow.follow_id == selected_follow.id

            selected_notification_by_id = notification_crud.get_notification_by_id(
                db_session,
                new_notification_about_follow.id,
            )

            assert new_notification_about_follow.id == selected_notification_by_id.id

    total_follow_count = 81

    for follow_id in range(1, total_follow_count + 1):
        notification_by_follow_id = notification_crud.get_notification_by_follow_id(
            db_session,
            follow_id,
        )

        notification_by_id = notification_crud.get_notification_by_id(
            db_session,
            notification_by_follow_id.id,
        )

        assert notification_by_follow_id == notification_by_id

        notification_crud.mark_as_read(
            db_session,
            notification_by_follow_id.id,
        )

        assert notification_by_follow_id.read is True


def test_create_and_get_notification_on_postlike_then_mark_as_read(
    client: TestClient,
    db_session: Session,
    fake_postlike: None,
):
    selected_post_count = 50
    total_user_count = 2

    for user_id in range(1, total_user_count + 1):
        for post_id in range(1, selected_post_count + 1):
            selected_post_like = post_crud.get_like(
                db_session,
                user_id_who_like=user_id,
                liked_post_id=post_id,
            )

            assert selected_post_like is not None

            new_notification_about_postlike = (
                notification_crud.create_notification_on_postlike(
                    db_session,
                    selected_post_like.id,
                    selected_post_like.liked_post.writer.id,
                )
            )

            assert hasattr(new_notification_about_postlike, "id")
            assert hasattr(new_notification_about_postlike, "created_at")
            assert hasattr(new_notification_about_postlike, "updated_at")
            assert hasattr(new_notification_about_postlike, "read")
            assert hasattr(new_notification_about_postlike, "follow_id")
            assert hasattr(new_notification_about_postlike, "post_like_id")
            assert hasattr(new_notification_about_postlike, "notified_user_id")
            assert hasattr(new_notification_about_postlike, NotificationType.post_like)
            assert new_notification_about_postlike.read is False
            assert new_notification_about_postlike.post_like_id == selected_post_like.id

            selected_notification_by_id = notification_crud.get_notification_by_id(
                db_session,
                new_notification_about_postlike.id,
            )

            assert new_notification_about_postlike == selected_notification_by_id

    for post_id in range(1, selected_post_count + 1):
        selected_notification_by_postlike_id = (
            notification_crud.get_notification_by_postlike_id(
                db_session,
                selected_post_like.id,
            )
        )

        selected_notification_by_id = notification_crud.get_notification_by_id(
            db_session,
            new_notification_about_postlike.id,
        )

        assert selected_notification_by_postlike_id == selected_notification_by_id

        notification_crud.mark_as_read(
            db_session,
            selected_notification_by_postlike_id.id,
        )

        assert new_notification_about_postlike.read is True


def test_get_notifications_on_follow_by_notified_user_id(
    client: TestClient,
    db_session: Session,
    fake_follow: None,
):
    total_user_count = 10
    for follower_id in range(1, total_user_count + 1):
        for following_id in range(1, total_user_count + 1):
            if follower_id == following_id:
                continue

            selected_follow = user_crud.get_follow(
                db_session,
                follower_id=follower_id,
                following_id=following_id,
            )

            notification_crud.create_notification_on_follow(
                db_session,
                selected_follow.id,
                selected_follow.follower_id,
            )

        results = notification_crud.get_notifications_by_notified_user_id(
            db_session,
            follower_id,
        )

        assert len(results) == 9


def test_get_notifications_on_postlike_by_notified_user_id(
    client: TestClient,
    db_session: Session,
    fake_postlike: None,
):
    selected_post_count = 50
    total_user_count = 2

    writer_id = 1

    for user_id in range(1, total_user_count + 1):
        for post_id in range(1, selected_post_count + 1):
            selected_post_like = post_crud.get_like(
                db_session,
                user_id_who_like=user_id,
                liked_post_id=post_id,
            )

            notification_crud.create_notification_on_postlike(
                db_session,
                selected_post_like.id,
                selected_post_like.liked_post.writer.id,
            )

    total_count = 0

    for skip in range(0, 100, 10):
        results = notification_crud.get_notifications_by_notified_user_id(
            db_session,
            writer_id,
            skip=skip,
        )
        total_count += len(results)
        assert len(results) == 10

    # 총 읽어온 알림의 수량 확인
    assert total_count == 100

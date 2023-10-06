from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from sns.users.repositories.db import user_crud
from sns.posts.repository import post_crud
from sns.notification.repository import notification_crud


def test_create_and_get_notification_then_change_is_read_state(
    client: TestClient,
    db_session: Session,
    fake_follow: None,
    fake_postlike: None,
):
    # notification about follow
    selected_follow = user_crud.get_follow(
        db_session,
        follower_id=2,
        following_id=1,
    )

    new_notification_about_follow = notification_crud.create_notification_on_follow(
        db_session,
        selected_follow.id,
    )

    selected_notification = notification_crud.get_notification_by_follow_id(
        db_session,
        selected_follow.id,
    )

    assert hasattr(new_notification_about_follow, "id")
    assert hasattr(new_notification_about_follow, "created_at")
    assert hasattr(new_notification_about_follow, "updated_at")
    assert hasattr(new_notification_about_follow, "is_read")
    assert hasattr(new_notification_about_follow, "follow_id")
    assert new_notification_about_follow.follow_id == selected_follow.id
    assert new_notification_about_follow.id == selected_notification.id
    assert hasattr(new_notification_about_follow, "post_like_id")
    assert new_notification_about_follow.is_read is False

    notification_crud.change_is_read_state(
        db_session,
        selected_notification.id,
    )

    assert new_notification_about_follow.is_read is True

    # notification about post_like
    user_id_used_for_postlike = 11
    selected_post_like = post_crud.get_like(
        db_session,
        who_like_id=user_id_used_for_postlike,
        like_target_id=1,
    )

    new_notification_about_postlike = notification_crud.create_notification_on_postlike(
        db_session,
        selected_post_like.id,
    )

    selected_notification = notification_crud.get_notification_by_postlike_id(
        db_session,
        selected_post_like.id,
    )

    assert hasattr(new_notification_about_postlike, "id")
    assert hasattr(new_notification_about_postlike, "created_at")
    assert hasattr(new_notification_about_postlike, "updated_at")
    assert hasattr(new_notification_about_postlike, "is_read")
    assert hasattr(new_notification_about_postlike, "follow_id")
    assert hasattr(new_notification_about_postlike, "post_like_id")
    assert new_notification_about_postlike.post_like_id == selected_post_like.id
    assert new_notification_about_postlike.id == selected_notification.id
    assert new_notification_about_postlike.is_read is False

    notification_crud.change_is_read_state(
        db_session,
        selected_notification.id,
    )

    assert new_notification_about_postlike.is_read is True

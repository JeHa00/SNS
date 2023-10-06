from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from sns.notification.repository import notification_crud


def test_change_is_read_state(
    client: TestClient,
    db_session: Session,
    fake_multi_follow_notification,
    fake_multi_postlike_notification,
):
    total_notifications_count = 214

    for id in range(1, total_notifications_count + 1):
        selected_notification = notification_crud.get_notification_by_id(db_session, id)

        assert selected_notification.is_read is False

        selected_notification = notification_crud.change_is_read_state(db_session, id)

        assert selected_notification.is_read is True

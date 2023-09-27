from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session

from sns.common.session import db
from sns.users.service import UserService
from sns.users.schema import Message, UserBase
from sns.notification.service import NotificationService
from sns.notification.schema import NotificationUpdate

router = APIRouter()


@router.patch(
    "/notifications/{notification_id}",
    response_model=Message,
    status_code=status.HTTP_200_OK,
)
def change_is_read_state_to_true(
    notification_id: int,
    is_read: NotificationUpdate,
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    notification_service: NotificationService = Depends(NotificationService),
    db: Session = Depends(db.get_db),
) -> Message:
    notification_service.change_is_read_state_to_true(
        db,
        notification_id,
        current_user.id,
    )
    return {"status": "success", "message": "상태가 읽음 표시로 변경되었습니다."}

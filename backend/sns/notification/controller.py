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
    """해당 id의 알림 읽기 상태를 읽음 상태로 변경합니다.

    Args:
        notification_id (int): 알림의 id
        is_read (NotificationUpdate): 객체 형태로 is_read의 값을 보낸다.
            - ex: {"is_read": True}

    Raises:
        HTTPException (403 FORBIDDEN): 수정 권한이 없는 경우
        HTTPException (500 INTERNAL SERVER ERROR): 알림 읽기 상태 변경에 실패한 경우

    Returns:
        Message: 변경 성공 시 성공 메세지를 반환
    """
    notification_service.change_is_read_state_to_true(
        db,
        notification_id,
        current_user.id,
    )
    return {"status": "success", "message": "상태가 읽음 표시로 변경되었습니다."}

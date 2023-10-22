from fastapi import APIRouter, status, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from redis.client import Redis

from sns.common.session import db, redis_db
from sns.users.service import UserService
from sns.users.schema import Message, UserBase
from sns.notification.service import NotificationService

router = APIRouter()


@router.patch(
    "/notifications/{notification_id}",
    response_model=Message,
    status_code=status.HTTP_200_OK,
)
def mark_as_read(
    notification_id: int,
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    notification_service: NotificationService = Depends(NotificationService),
    db: Session = Depends(db.get_db),
) -> Message:
    """notification_id에 해당하는 알림 읽기 상태를 읽음 상태로 변경한다.

    Args:
        - notification_id (int): 알림의 id

    Raises:
        - HTTPException (403 FORBIDDEN): 수정 권한이 없는 경우
        - HTTPException (500 INTERNAL SERVER ERROR): 알림 읽기 상태 변경에 실패한 경우

    Returns:
        - Message: 성공 메세지를 반환
    """
    notification_service.mark_as_read(
        db,
        notification_id,
        current_user.id,
    )
    return {"status": "success", "message": "상태가 읽음 표시로 변경되었습니다."}


@router.get(
    "/notifications",
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_event(
    request: Request,
    notification_service: NotificationService = Depends(NotificationService),
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    redis_db: Redis = Depends(redis_db.get_db),
) -> StreamingResponse:
    """실시간으로 생성된 알림 데이터를 클라이언트에게 전달한다.
    없으면 전달하지 않는다. 새로 생성된 알림 데이터가 존재할 경우 문자열 타입의 알림 데이터를 1초 간격으로 전달한다.

    Returns:
        - StreamingResponse: 문자열 타입의 알림 데이터
    """
    return await notification_service.send_event(
        redis_db,
        request,
        current_user.email,
    )

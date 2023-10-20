from fastapi import status, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from redis.client import Redis
import asyncio

from sns.common.config import settings
from sns.notification.repository import notification_crud, RedisQueue
from sns.notification.enums import NotificationType


class NotificationService:
    def mark_as_read(
        self,
        db: Session,
        notification_id: int,
        current_user_id: int,
    ) -> bool:
        """알림의 읽기 상태를 읽음 상태로 변경한다.

        Args:
            db (Session): db session
            notification_id (int): Notification의 id

        Raises:
            HTTPException (403 FORBIDDEN): 수정 권한이 없는 경우
            HTTPException (500 INTERNAL SERVER ERROR): 알림 읽기 상태 변경에 실패한 경우

        Returns:
            bool: 성공 시 True
        """
        selected_notification = notification_crud.get_notification_by_id(
            db,
            notification_id,
        )

        if selected_notification.notified_user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="수정 권한이 없습니다.",
            )

        try:
            notification_crud.mark_as_read(
                db,
                notification_id,
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="알림 읽기 상태 변경에 실패했습니다.",
            )

        return True

    async def send_event(
        self,
        redis_db: Redis,
        request: Request,
        current_user_email: str,
    ) -> StreamingResponse:
        """current_user_email을 key 값으로 가지는 queue에 event가 존재하는지 확인한다.
        존재하면 클라이언트에게 자동적으로 알림 데이터를 보내준다.

        Args:
            redis_db (Redis): redis db
            request (Request): request 객체
            current_user_email (str): 현재 로그인한 유저의 이메일

        Returns:
            StreamingResponse: _description_

        Yields:
            Iterator[StreamingResponse]: _description_
        """
        headers = {
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Origin": "*",
        }

        message_queue = RedisQueue(
            redis_db,
            f"notification_useremail:{current_user_email}",
        )

        async def detect_and_send_event():
            while True:
                if await request.is_disconnected():
                    break

                if not message_queue.empty:
                    message = message_queue.pop()

                    last_event_id = request.headers.get(
                        "lastEventId",
                        message.get("created_at"),
                    )

                    event_type = (
                        f"event: {NotificationType.follow}\n"
                        if message.get("type") == f"{NotificationType.follow}"
                        else f"event: {NotificationType.post_like}\n"
                    )
                    identifier = f"id: {last_event_id}\n"
                    retry = f"retry: {settings.TIME_TO_RETRY_CONNECTION}\n"
                    data = f"data: {message}\n\n"

                    event = event_type + identifier + retry + data

                    yield event

                    await asyncio.sleep(1)

                await asyncio.sleep(5)

        return StreamingResponse(
            detect_and_send_event(),
            media_type="text/event-stream",
            headers=headers,
        )


notification_service = NotificationService()

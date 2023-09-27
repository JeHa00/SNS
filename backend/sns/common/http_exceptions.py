from fastapi import HTTPException, status


class CommonHTTPExceptions:
    USER_NOT_FOUND_ERROR = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "code": "USER_NOT_FOUND",
            "message": "해당되는 유저를 찾을 수 없습니다.",
        },
    )

    POST_NOT_FOUND_ERROR = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "code": "POST_NOT_FOUND",
            "message": "해당되는 글을 찾을 수 없습니다.",
        },
    )

    COMMENT_NOT_FOUND_ERROR = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "code": "COMMENT_NOT_FOUND",
            "message": "해당되는 댓글을 찾을 수 없습니다.",
        },
    )

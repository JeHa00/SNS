from enum import StrEnum, auto


class NotificationType(StrEnum):
    post_like = auto()
    follow = auto()

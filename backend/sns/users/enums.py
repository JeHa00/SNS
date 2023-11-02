from enum import StrEnum, auto


class EmailTemplateType(StrEnum):
    new_account = auto()
    reset_password = auto()


class FileType(StrEnum):
    html = auto()

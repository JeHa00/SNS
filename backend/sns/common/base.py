from sqlalchemy import Column, Integer, TIMESTAMP, func
from sqlalchemy.orm import as_declarative, declared_attr


@as_declarative()
class Base:
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class BaseMixin:
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=func.now(),
        onupdate=func.now(),
    )

from sqlalchemy import Column, Integer, TIMESTAMP, func

class BaseMixin:
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.now(), onupdate=func.now())

    def __tablename__(cls) -> str:
        return cls.__name__.lower() 
    
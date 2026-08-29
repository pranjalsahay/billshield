from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime
)

from sqlalchemy.sql import func

from database import Base


class Block(Base):
    __tablename__ = "blocks"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    block_number = Column(
        Integer,
        unique=True,
        nullable=False,
        index=True
    )

    bill_id = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    bill_hash = Column(
        String(64),
        nullable=False
    )

    previous_hash = Column(
        String(64),
        nullable=False
    )

    block_hash = Column(
        String(64),
        unique=True,
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
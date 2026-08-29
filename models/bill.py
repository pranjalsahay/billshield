from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    ForeignKey
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from database import Base


class Bill(Base):
    __tablename__ = "bills"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    bill_id = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    student_id = Column(
        String(50),
        ForeignKey("students.student_id"),
        nullable=False
    )

    amount = Column(
        Float,
        nullable=False
    )

    fee_type = Column(
        String(100),
        nullable=False
    )

    billing_month = Column(
        String(20),
        nullable=False
    )

    issue_date = Column(
        Date,
        nullable=False
    )

    due_date = Column(
        Date,
        nullable=False
    )

    # SHA-256 cryptographic fingerprint
    bill_hash = Column(
        String(64),
        unique=True,
        nullable=True,
        index=True
    )

    # RSA digital signature
    digital_signature = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    student = relationship(
        "Student",
        back_populates="bills"
    )
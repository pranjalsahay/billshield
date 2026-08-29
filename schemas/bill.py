from datetime import date
from pydantic import BaseModel, ConfigDict


class BillCreate(BaseModel):
    bill_id: str
    student_id: str
    amount: float
    fee_type: str
    billing_month: str
    issue_date: date
    due_date: date


class BillResponse(BaseModel):
    id: int
    bill_id: str
    student_id: str
    amount: float
    fee_type: str
    billing_month: str
    issue_date: date
    due_date: date

    # SHA-256 cryptographic fingerprint
    bill_hash: str | None = None

    # RSA digital signature
    digital_signature: str | None = None

    model_config = ConfigDict(from_attributes=True)
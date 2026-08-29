import hashlib
import json


def generate_bill_hash(
    bill_id: str,
    student_id: str,
    amount: float,
    fee_type: str,
    billing_month: str,
    issue_date,
    due_date
):
    # Create deterministic bill data
    bill_data = {
        "bill_id": bill_id,
        "student_id": student_id,
        "amount": amount,
        "fee_type": fee_type,
        "billing_month": billing_month,
        "issue_date": str(issue_date),
        "due_date": str(due_date)
    }

    # Convert dictionary into consistent JSON
    bill_string = json.dumps(
        bill_data,
        sort_keys=True
    )

    # Generate SHA-256 hash
    bill_hash = hashlib.sha256(
        bill_string.encode("utf-8")
    ).hexdigest()

    return bill_hash
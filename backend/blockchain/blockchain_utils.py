import hashlib


def generate_block_hash(
    block_number: int,
    bill_id: str,
    bill_hash: str,
    previous_hash: str
):
    data = (
        f"{block_number}|"
        f"{bill_id}|"
        f"{bill_hash}|"
        f"{previous_hash}"
    )

    return hashlib.sha256(
        data.encode("utf-8")
    ).hexdigest()
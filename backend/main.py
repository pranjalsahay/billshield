from typing import List

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal

# Import all models so SQLAlchemy registers them
import models

from models.student import Student
from models.bill import Bill
from models.block import Block

from schemas.student import StudentCreate, StudentResponse
from schemas.bill import BillCreate, BillResponse

from security.hash_utils import generate_bill_hash
from security.digital_signature import (
    sign_bill_hash,
    verify_bill_signature
)

from blockchain.blockchain_utils import generate_block_hash


# ===================================================
# CREATE DATABASE TABLES
# ===================================================

Base.metadata.create_all(bind=engine)


# ===================================================
# FASTAPI APPLICATION
# ===================================================

app = FastAPI(
    title="BillShield AI",
    description="AI-Powered Tamper-Proof College Bill Verification System",
    version="1.0.0"
)


# ===================================================
# DATABASE SESSION
# ===================================================

def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ===================================================
# BASIC API
# ===================================================

@app.get("/")
def root():
    return {
        "message": "BillShield AI API is running",
        "status": "online"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ===================================================
# DATABASE CONNECTION TEST
# ===================================================

@app.get("/database-test")
def database_test():

    try:
        with engine.connect() as connection:

            result = connection.execute(
                text("SELECT current_database();")
            )

            database_name = result.scalar()

        return {
            "database": database_name,
            "status": "connected"
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }


# ===================================================
# STUDENT APIs
# ===================================================


# ---------------------------------------------------
# CREATE STUDENT
# ---------------------------------------------------

@app.post("/students", response_model=StudentResponse)
def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db)
):

    # Check whether student ID already exists
    existing_student = (
        db.query(Student)
        .filter(Student.student_id == student.student_id)
        .first()
    )

    if existing_student:
        raise HTTPException(
            status_code=400,
            detail="Student ID already exists"
        )

    # Check whether email already exists
    existing_email = (
        db.query(Student)
        .filter(Student.email == student.email)
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    # Create student
    new_student = Student(
        student_id=student.student_id,
        full_name=student.full_name,
        email=student.email,
        department=student.department
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return new_student


# ---------------------------------------------------
# GET ALL STUDENTS
# ---------------------------------------------------

@app.get("/students", response_model=List[StudentResponse])
def get_students(
    db: Session = Depends(get_db)
):

    students = db.query(Student).all()

    return students


# ===================================================
# BILL APIs
# ===================================================


# ---------------------------------------------------
# CREATE BILL + DIGITAL SIGNATURE + BLOCKCHAIN BLOCK
# ---------------------------------------------------

@app.post("/bills", response_model=BillResponse)
def create_bill(
    bill: BillCreate,
    db: Session = Depends(get_db)
):

    # -----------------------------------------------
    # CHECK WHETHER STUDENT EXISTS
    # -----------------------------------------------

    student = (
        db.query(Student)
        .filter(Student.student_id == bill.student_id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )


    # -----------------------------------------------
    # CHECK WHETHER BILL ID ALREADY EXISTS
    # -----------------------------------------------

    existing_bill = (
        db.query(Bill)
        .filter(Bill.bill_id == bill.bill_id)
        .first()
    )

    if existing_bill:
        raise HTTPException(
            status_code=400,
            detail="Bill ID already exists"
        )


    # -----------------------------------------------
    # GENERATE SHA-256 HASH
    # -----------------------------------------------

    bill_hash = generate_bill_hash(
        bill_id=bill.bill_id,
        student_id=bill.student_id,
        amount=bill.amount,
        fee_type=bill.fee_type,
        billing_month=bill.billing_month,
        issue_date=bill.issue_date,
        due_date=bill.due_date
    )


    # -----------------------------------------------
    # GENERATE RSA DIGITAL SIGNATURE
    # -----------------------------------------------

    digital_signature = sign_bill_hash(
        bill_hash
    )


    # -----------------------------------------------
    # CREATE BILL
    # -----------------------------------------------

    new_bill = Bill(
        bill_id=bill.bill_id,
        student_id=bill.student_id,
        amount=bill.amount,
        fee_type=bill.fee_type,
        billing_month=bill.billing_month,
        issue_date=bill.issue_date,
        due_date=bill.due_date,
        bill_hash=bill_hash,
        digital_signature=digital_signature
    )

    db.add(new_bill)


    # =================================================
    # BLOCKCHAIN LOGIC
    # =================================================


    # -----------------------------------------------
    # GET LAST BLOCK
    # -----------------------------------------------

    last_block = (
        db.query(Block)
        .order_by(Block.block_number.desc())
        .first()
    )


    # -----------------------------------------------
    # CREATE GENESIS BLOCK
    # -----------------------------------------------

    if last_block is None:

        block_number = 1

        previous_hash = "0" * 64


    # -----------------------------------------------
    # CREATE NORMAL BLOCK
    # -----------------------------------------------

    else:

        block_number = last_block.block_number + 1

        previous_hash = last_block.block_hash


    # -----------------------------------------------
    # GENERATE BLOCK HASH
    # -----------------------------------------------

    block_hash = generate_block_hash(
        block_number=block_number,
        bill_id=bill.bill_id,
        bill_hash=bill_hash,
        previous_hash=previous_hash
    )


    # -----------------------------------------------
    # CREATE BLOCK
    # -----------------------------------------------

    new_block = Block(
        block_number=block_number,
        bill_id=bill.bill_id,
        bill_hash=bill_hash,
        previous_hash=previous_hash,
        block_hash=block_hash
    )

    db.add(new_block)


    # -----------------------------------------------
    # SAVE BILL + BLOCK
    # -----------------------------------------------

    try:

        db.commit()

        db.refresh(new_bill)
        db.refresh(new_block)

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to create bill and blockchain block: "
                f"{str(e)}"
            )
        )


    return new_bill


# ---------------------------------------------------
# GET ALL BILLS
# ---------------------------------------------------

@app.get("/bills", response_model=List[BillResponse])
def get_bills(
    db: Session = Depends(get_db)
):

    bills = db.query(Bill).all()

    return bills


# ---------------------------------------------------
# GET SPECIFIC BILL
# ---------------------------------------------------

@app.get("/bills/{bill_id}", response_model=BillResponse)
def get_bill(
    bill_id: str,
    db: Session = Depends(get_db)
):

    bill = (
        db.query(Bill)
        .filter(Bill.bill_id == bill_id)
        .first()
    )

    if not bill:
        raise HTTPException(
            status_code=404,
            detail="Bill not found"
        )

    return bill


# ===================================================
# BILL VERIFICATION
# ===================================================


# ---------------------------------------------------
# VERIFY BILL
# SHA-256 + DIGITAL SIGNATURE + BLOCKCHAIN
# ---------------------------------------------------

@app.get("/verify-bill/{bill_id}")
def verify_bill(
    bill_id: str,
    db: Session = Depends(get_db)
):

    # -----------------------------------------------
    # FIND BILL
    # -----------------------------------------------

    bill = (
        db.query(Bill)
        .filter(Bill.bill_id == bill_id)
        .first()
    )

    if not bill:
        raise HTTPException(
            status_code=404,
            detail="Bill not found"
        )


    # -----------------------------------------------
    # CHECK BILL HASH
    # -----------------------------------------------

    if not bill.bill_hash:

        return {
            "bill_id": bill.bill_id,
            "status": "UNVERIFIABLE",
            "message": (
                "This bill does not contain "
                "cryptographic protection"
            )
        }


    # -----------------------------------------------
    # GENERATE CURRENT HASH
    # -----------------------------------------------

    current_hash = generate_bill_hash(
        bill_id=bill.bill_id,
        student_id=bill.student_id,
        amount=bill.amount,
        fee_type=bill.fee_type,
        billing_month=bill.billing_month,
        issue_date=bill.issue_date,
        due_date=bill.due_date
    )


    # -----------------------------------------------
    # VERIFY BILL DATA INTEGRITY
    # -----------------------------------------------

    hash_valid = (
        current_hash == bill.bill_hash
    )


    # -----------------------------------------------
    # VERIFY DIGITAL SIGNATURE
    # -----------------------------------------------

    signature_valid = False

    if bill.digital_signature:

        signature_valid = verify_bill_signature(
            bill.bill_hash,
            bill.digital_signature
        )


    # -----------------------------------------------
    # FIND BLOCKCHAIN BLOCK
    # -----------------------------------------------

    block = (
        db.query(Block)
        .filter(Block.bill_id == bill.bill_id)
        .first()
    )


    blockchain_valid = False

    if block:

        calculated_block_hash = generate_block_hash(
            block_number=block.block_number,
            bill_id=block.bill_id,
            bill_hash=block.bill_hash,
            previous_hash=block.previous_hash
        )

        blockchain_valid = (
            calculated_block_hash == block.block_hash
        )


    # -----------------------------------------------
    # FINAL VERIFICATION
    # -----------------------------------------------

    if (
        hash_valid
        and signature_valid
        and blockchain_valid
    ):

        return {
            "bill_id": bill.bill_id,
            "status": "AUTHENTIC",
            "message": (
                "Bill hash, digital signature and "
                "blockchain integrity verified successfully"
            ),

            "hash_verification": "VALID",

            "digital_signature": "VALID",

            "blockchain_verification": "VALID",

            "stored_hash": bill.bill_hash,

            "current_hash": current_hash,

            "block_number": block.block_number
        }


    # -----------------------------------------------
    # TAMPERED OR INVALID
    # -----------------------------------------------

    return {
        "bill_id": bill.bill_id,

        "status": "TAMPERED_OR_INVALID",

        "message": (
            "One or more security verification "
            "checks failed"
        ),

        "hash_verification": (
            "VALID"
            if hash_valid
            else "INVALID"
        ),

        "digital_signature": (
            "VALID"
            if signature_valid
            else "INVALID"
        ),

        "blockchain_verification": (
            "VALID"
            if blockchain_valid
            else "INVALID"
        ),

        "stored_hash": bill.bill_hash,

        "current_hash": current_hash
    }
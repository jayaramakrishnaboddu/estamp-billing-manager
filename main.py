from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models
import schemas
from database import engine, get_db
from fastapi import UploadFile, File,Header, Query
import ocr_service_tess
from fastapi import Query,UploadFile, File
from datetime import date, datetime, time
from auth import verify_password
from fastapi.responses import FileResponse
import pandas as pd
from passlib.context import CryptContext
import subprocess
import os
import tempfile
from dotenv import load_dotenv

load_dotenv()

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# Create database tables automatically on launch
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="E-Stamp Automated Billing & Accounting System API")
def calculate_service_charge(stamp_duty: int) -> int:

    charge_map = {
        10: 20,
        50: 20,
        100: 30,
        200: 60,
        500: 100,
        1000: 100
    }

    return charge_map.get(stamp_duty, 20)

@app.post("/customers/", response_model=schemas.CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    db_customer = db.query(models.Customer).filter(models.Customer.name == customer.name).first()
    if db_customer:
        raise HTTPException(status_code=400, detail="Customer name already registered.")
    
    new_customer = models.Customer(name=customer.name, phone=customer.phone)
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer


@app.post("/transactions/", response_model=schemas.TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(tx: schemas.TransactionCreate, db: Session = Depends(get_db)):
    # 1. Enforce strict uniqueness on certificate numbers to prevent duplicate pastes
    db_tx = db.query(models.Transaction).filter(models.Transaction.certificate_number == tx.certificate_number).first()
    if db_tx:
        raise HTTPException(status_code=400, detail="Duplicate stamp: This certificate code has already been processed.")

    # 2. Extract service parameters dynamically
    service_fee = calculate_service_charge(tx.stamp_duty)
    grand_total = tx.stamp_duty + service_fee

    # 3. Handle debt account updates if logged via Khata accounts
    if tx.payment_mode.strip().lower() == "debt":
        if not tx.customer_id:
            raise HTTPException(status_code=400, detail="Customer ID is strictly required for Debt tracking transactions.")
        
        customer = db.query(models.Customer).filter(models.Customer.id == tx.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Selected debt ledger client profile not found.")
        
        # Increment rolling debt balance automatically
        customer.current_balance += grand_total
        print(
        f"Customer={customer.name}, "
        f"OldBalance={customer.current_balance - grand_total}, "
        f"Added={grand_total}, "
        f"NewBalance={customer.current_balance}"
        )

    # 4. Save entry to ledger
    new_tx = models.Transaction(
        certificate_number=tx.certificate_number,
        stamp_duty=tx.stamp_duty,
        service_charge=service_fee,
        total_collected=grand_total,
        payment_mode=tx.payment_mode,
        processed_by=tx.processed_by,
        customer_id=tx.customer_id if tx.payment_mode.strip().lower() == "debt" else None
    )
    db.add(new_tx)
    db.commit()
    db.refresh(new_tx)
    return new_tx
@app.post("/process-stamp/", response_model=schemas.TransactionCreate)
async def process_stamp_image(file: UploadFile = File(...)):
    """
    Accepts an uploaded image file from the clipboard, processes it with Gemini,
    and returns a pre-filled transaction transaction object for the worker to confirm.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a valid image snippet.")
    try:
        image_bytes = await file.read()
        extracted_data = ocr_service_tess.analyze_stamp_screenshot(image_bytes)
        return schemas.TransactionCreate(
            certificate_number=extracted_data.certificate_number,
            stamp_duty=extracted_data.stamp_duty_amount,
            payment_mode="Cash"
        )
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Image processing anomaly: {str(e)}")
    
@app.get("/analytics/daily-summary/")
def get_daily_summary(db: Session = Depends(get_db)):
    """
    Calculates live, real-time financial reconciliation metrics for the current day.
    """
    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)

    # Fetch all transactions recorded today
    todays_txs = db.query(models.Transaction).filter(
        models.Transaction.timestamp >= today_start,
        models.Transaction.timestamp <= today_end
    ).all()

    # Initialize live accounting metrics
    cash_collected = 0
    phonepe_collected = 0
    debt_incurred = 0
    total_net_profit = 0

    for tx in todays_txs:
        total_net_profit += tx.service_charge
        
        mode = tx.payment_mode.strip().lower()
        if mode == "cash":
            cash_collected += tx.total_collected
        elif mode == "phonepe":
            phonepe_collected += tx.total_collected
        elif mode == "debt":
            debt_incurred += tx.total_collected

    return {
        "cash_expected": cash_collected,
        "phonepe_verified": phonepe_collected,
        "debt_incurred": debt_incurred,
        "net_profit": total_net_profit,
        "stamp_count": len(todays_txs)
    }

# Endpoint to fetch real active customer profiles for the dropdown
@app.get("/customers/")
def list_customers(db: Session = Depends(get_db)):
    return db.query(models.Customer).all()
@app.get("/transactions/")
def get_transactions(db: Session = Depends(get_db)):
    return db.query(models.Transaction)\
             .order_by(models.Transaction.id.desc())\
             .all()
@app.get("/analytics/daily-summary/")
def get_daily_summary(x_user_role: str = Header(...), db: Session = Depends(get_db)):
    if x_user_role.strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Access Denied: Administrative privileges required.")

    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)
    todays_txs = db.query(models.Transaction).filter(models.Transaction.timestamp >= today_start, models.Transaction.timestamp <= today_end).all()

    cash = sum(t.total_collected for t in todays_txs if t.payment_mode.lower() == "cash")
    phonepe = sum(t.total_collected for t in todays_txs if t.payment_mode.lower() == "phonepe")
    debt = sum(t.total_collected for t in todays_txs if t.payment_mode.lower() == "debt")
    profit = sum(t.service_charge for t in todays_txs)

    return {
        "cash_expected": cash,
        "phonepe_verified": phonepe,
        "debt_incurred": debt,
        "net_profit": profit,
        "stamp_count": len(todays_txs)
    }

# ==========================================
# ROLE-BASED TRANSACTION HISTORY VIEW
# ==========================================
@app.get("/transactions/")
def get_all_transactions(x_user_role: str = Header(...), db: Session = Depends(get_db)):
    txs = db.query(models.Transaction).order_by(models.Transaction.timestamp.desc()).all()
    
    # If worker logs in, serve them masked data structures devoid of profit margins
    if x_user_role.strip().lower() == "worker":
        return [
            {
                "id": t.id,
                "certificate_number": t.certificate_number,
                "stamp_duty": t.stamp_duty,
                "total_collected": t.total_collected,
                "payment_mode": t.payment_mode,
                "timestamp": t.timestamp
            } for t in txs
        ]
    return txs # Admins receive the raw dictionary data complete with service charges

# ==========================================
# KHATA SPECIFIC ACCOUNT HISTORY ENDPOINT
# ==========================================
@app.get("/customers/{customer_id}/statement/")
def get_customer_statement(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer profile missing.")
    
    txs = db.query(models.Transaction).filter(models.Transaction.customer_id == customer_id).order_by(models.Transaction.timestamp.desc()).all()
    return {
        "customer_name": customer.name,
        "balance_due": customer.current_balance,
        "history": txs
    }

# ==========================================
# SECURE TRANSACTION DELETION (WITH BALANCING)
# ==========================================
@app.delete("/transactions/{tx_id}/")
def delete_transaction(tx_id: int, x_user_role: str = Header(...), db: Session = Depends(get_db)):
    if x_user_role.strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Critical Operation Denied: Workers cannot erase entries.")

    tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Target transaction record not found.")

    # Roll back credit accounts if deleting a debt transaction
    if tx.payment_mode.lower() == "debt" and tx.customer_id:
        customer = db.query(models.Customer).filter(models.Customer.id == tx.customer_id).first()
        if customer:
            customer.current_balance -= tx.total_collected

    db.delete(tx)
    db.commit()
    return {"detail": "Transaction successfully struck off and balances re-adjusted."}
@app.post("/login/", response_model=schemas.LoginResponse)
def login(
    credentials: schemas.LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.username == credentials.username
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not verify_password(
        credentials.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    return {
        "username": user.username,
        "role": user.role
    }
@app.post("/payments/")
def record_payment(
    payment: schemas.PaymentCreate,
    db: Session = Depends(get_db)
):
    customer = db.query(models.Customer).filter(
        models.Customer.id == payment.customer_id
    ).first()

    if not customer:
        raise HTTPException(404, "Customer not found")

    if payment.amount <= 0:
        raise HTTPException(400, "Invalid amount")
    previous_due = customer.current_balance
    if payment.amount > previous_due:
        raise HTTPException(
            status_code=400,
            detail=f"Payment exceeds outstanding due of ₹{previous_due}"
        )
    remaining_due = previous_due - payment.amount
    customer.current_balance = remaining_due
    new_payment = models.Payment(
        customer_id=payment.customer_id,
        previous_due=previous_due,
        amount_paid=payment.amount,
        remaining_due=remaining_due,
        amount=payment.amount
    )

    db.add(new_payment)
    db.commit()
    db.refresh(customer)
    
    return {
        "message": "Payment recorded successfully",
        "previous_due": previous_due,
        "amount_paid": payment.amount,
        "remaining_due": remaining_due
    }
@app.delete("/customers/{customer_id}/")
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db)
):
    customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    # Prevent deletion if money is still owed
    if customer.current_balance > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete customer. Outstanding balance ₹{customer.current_balance}"
        )

    db.delete(customer)
    db.commit()

    return {"message": "Customer deleted successfully"}
@app.get("/export/daily-report/")
def export_daily_report(
    db: Session = Depends(get_db)
):
    today = date.today()
    transactions = db.query(models.Transaction).filter(models.Transaction.timestamp >= today).all()

    data = []

    for tx in transactions:
        data.append({
            "Certificate Number": tx.certificate_number,
            "Stamp Duty": tx.stamp_duty,
            "Payment Mode": tx.payment_mode,
            "Timestamp": tx.timestamp
        })

    df = pd.DataFrame(data)
    filename = f"daily_report_{today}.xlsx"

    df.to_excel(
        filename,
        index=False
    )

    return FileResponse(
        path=filename,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
@app.get("/users/")
def get_users(
    db: Session = Depends(get_db)
):
    users = db.query(models.User).all()

    return [
        {
            "id": user.id,
            "username": user.username,
            "role": user.role
        }
        for user in users
    ]
@app.post("/users/")
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):

    existing = db.query(models.User).filter(
        models.User.username == user.username
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    hashed_password = pwd_context.hash(
        user.password_hash
    )

    new_user = models.User(
        username=user.username,
        password_hash=hashed_password,
        role=user.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully"
    }
@app.put("/users/password/")
def update_password(
    payload: schemas.PasswordUpdate,
    db: Session = Depends(get_db)
):

    user = db.query(models.User).filter(
        models.User.id == payload.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Verify old password
    if not pwd_context.verify(
        payload.old_password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )

    user.password_hash = pwd_context.hash(
        payload.new_password
    )

    db.commit()

    return {
        "message": "Password updated successfully"
    }
@app.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):

    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.role == "admin":
        raise HTTPException(
            status_code=400,
            detail="Admin user cannot be deleted"
        )

    db.delete(user)
    db.commit()

    return {
        "message": "User deleted successfully"
    }
@app.get("/backup/")
def backup_database():

    os.makedirs("backups", exist_ok=True)

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_file = (
        f"backups/backup_{timestamp}.sql"
    )

    subprocess.run(
        [
            r"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe",
            "-U",
            "postgres",
            "-d",
            "estamp",
            "-f",
            backup_file
        ],
        env={
            **os.environ,
            "PGPASSWORD": "loveusitha19"
        }
    )

    return FileResponse(
        backup_file,
        filename=os.path.basename(
            backup_file
        ),
        media_type="application/sql"
    )
@app.post("/restore/")
async def restore_database(
    file: UploadFile = File(...)
):

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".sql"
    )

    contents = await file.read()

    with open(temp_file.name, "wb") as f:
        f.write(contents)

    subprocess.run(
        [
            r"C:\Program Files\PostgreSQL\18\bin\psql.exe",
            "-U",
            "postgres",
            "-d",
            "estamp",
            "-f",
            temp_file.name
        ],
        env={
            **os.environ,
            "PGPASSWORD": "loveusitha19"
        }
    )

    return {
        "message": "Database restored successfully"
    }
@app.get("/customers/{customer_id}/payments/")
def get_customer_payments(
    customer_id: int,
    db: Session = Depends(get_db)
):
    payments = (
        db.query(models.Payment)
        .filter(
            models.Payment.customer_id == customer_id
        )
        .order_by(
            models.Payment.timestamp.desc()
        )
        .all()
    )

    return payments
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime,Boolean
from sqlalchemy.orm import relationship
import datetime
from database import Base
from datetime import datetime
from sqlalchemy import DateTime
from zoneinfo import ZoneInfo

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)

    customer_id = Column(
        Integer,
        ForeignKey("customers.id")
    )
    amount = Column(Integer) 

    previous_due = Column(Integer)

    amount_paid = Column(Integer)

    remaining_due = Column(Integer)

    timestamp = Column(DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Kolkata")))
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="worker") # 'admin' or 'worker'
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    current_balance = Column(Integer, default=0)  # Calculated in paise/cents or flat rupees

    # Relationship to track all debt entries linked to this customer
    transactions = relationship("Transaction", back_populates="customer")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    certificate_number = Column(String, unique=True, index=True, nullable=False)
    stamp_duty = Column(Integer, nullable=False)          # Base stamp rate (e.g., 10, 50, 100)
    service_charge = Column(Integer, nullable=False)      # Calculated automatically (+20, +30)
    total_collected = Column(Integer, nullable=False)     # stamp_duty + service_charge
    payment_mode = Column(String, nullable=False)         # 'Cash', 'PhonePe', or 'Debt'
    timestamp = Column(DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Kolkata")))
    processed_by = Column(String, nullable=True)

    # Foreign key link for Debt payments
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    
    customer = relationship("Customer", back_populates="transactions")
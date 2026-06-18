from pydantic import BaseModel
from typing import List,Optional
from datetime import datetime
class PaymentCreate(BaseModel):
    customer_id: int
    amount: int
class KhataCustomerSummary(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    current_balance: int
class WorkerTransactionResponse(BaseModel):
    id: int
    certificate_number: str
    stamp_duty: int
    total_collected: int # Notice service_charge is hidden here!
    payment_mode: str
    timestamp: datetime
# --- Customer Schemas ---
class CustomerBase(BaseModel):
    name: str
    phone: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int
    current_balance: int

    class Config:
        from_attributes = True


# --- Transaction Schemas ---
class TransactionCreate(BaseModel):
    certificate_number: str
    stamp_duty: int
    payment_mode: str  # 'Cash', 'PhonePe', 'Debt'
    customer_id: Optional[int] = None  # Mandatory only if payment_mode is 'Debt'
    processed_by: str |None = None 

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    username: str
    role: str
class PaymentCreate(BaseModel):
    customer_id: int
    amount: int
class UserCreate(BaseModel):
    username: str
    password_hash: str
    role: str
class PasswordUpdate(BaseModel):
    user_id: int
    old_password: str
    new_password: str
class UserDelete(BaseModel):
    user_id: int
class TransactionResponse(BaseModel):
    id: int
    certificate_number: str
    stamp_duty: int
    service_charge: int
    total_collected: int
    payment_mode: str
    timestamp: datetime
    customer_id: Optional[int] = None
    processed_by: str|None=None
        
    class Config:
        from_attributes = True

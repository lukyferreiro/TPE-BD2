from pydantic import BaseModel, constr
import datetime

EMAIL_REGEX=r'^[\w\.-]{0,64}@[\w\.-]+\.\w{0,255}$'
AFK_KEY_TYPE_REGEX=r"^(email|cuit|phone_number|random)$"

class User(BaseModel):
    name: str
    password: str
    email: constr(regex = EMAIL_REGEX)
    isBusiness: bool

class FinancialEntity(BaseModel):
    apiLink: str

class AFK_Key(BaseModel):
    keyValue: str
    keyType: constr(regex=AFK_KEY_TYPE_REGEX)
    financialId: int

class Transaction(BaseModel):
    AFK_key_from: str
    AFK_key_to: str
    date: datetime.datetime
    amount: float

class EditUser(BaseModel):
    name: str
    isBusiness: bool



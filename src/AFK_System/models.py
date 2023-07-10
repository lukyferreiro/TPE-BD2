from pydantic import BaseModel, constr, EmailStr
import datetime

EMAIL_REGEX=r'^[\w\.-]{0,64}@[\w\.-]+\.\w{0,255}$'
CBU_REGEX = r"^[0-9]{22}$"

class PostUser(BaseModel):
    name: str
    password: str
    email: EmailStr
    isBusiness: bool

class PostFinancialEntity(BaseModel):
    financialId: str
    name: str
    apiLink: str

class PostAfkKey(BaseModel):
    value: str
    cbu: constr(pattern=CBU_REGEX)

class PostTransaction(BaseModel):
    afk_key_from: str
    afk_key_to: str
    amount: float

class PutUser(BaseModel):
    name: str
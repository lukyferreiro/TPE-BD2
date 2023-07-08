from pydantic import BaseModel, constr
import datetime

EMAIL_REGEX=r'^[\w\.-]{0,64}@[\w\.-]+\.\w{0,255}$'
AFK_KEY_TYPE_REGEX=r"^(email|cuit|phone_number|random)$"
CBU_REGEX = r"^[0-9]{22}$"

class PostUser(BaseModel):
    name: str
    password: str
    email: constr(regex = EMAIL_REGEX)
    isBusiness: bool

class PostFinancialEntity(BaseModel):
    financialId: str
    name: str
    apiLink: str

class PostAfkKey(BaseModel):
    value: str
    keyType: constr(regex=AFK_KEY_TYPE_REGEX)
    cbu: constr(regex=CBU_REGEX)

class PostTransaction(BaseModel):
    afk_key_from: str
    afk_key_to: str
    amount: float

class PutUser(BaseModel):
    name: str
    isBusiness: bool



from pydantic import BaseModel, constr
from typing import Optional

CBU_REGEX = r"^[0-9]{22}$"

class Account(BaseModel):
    cbu: constr(regex = CBU_REGEX)
    username: str
    balance: float
    AFK_key: Optional[str]

class PostAmount(BaseModel):
    amount: float
    AFK_key: str
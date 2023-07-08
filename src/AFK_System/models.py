from pydantic import BaseModel, constr
import datetime


class Transaction(BaseModel):
    AFK_key_from: str
    AFK_key_to: str
    date: datetime.datetime
    amount: float

class EditUser(BaseModel):
    name: str
    isBusiness: bool



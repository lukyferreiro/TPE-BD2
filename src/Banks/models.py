from pydantic import BaseModel, constr

CBU_REGEX = r"^[0-9]{22}$"

class PostAmount(BaseModel):
    amount: float
    afk_key: str

class PutLink(BaseModel):
    afk_key: str
    cbu: constr(pattern=CBU_REGEX)

class PutUnlink(BaseModel):
    afk_key: str


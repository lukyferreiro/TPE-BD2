from fastapi import FastAPI, Path
from models import *
from postgre import *

app = FastAPI()

#-----------------------------POST-----------------------------

@app.post("/accounts")
def create_account(account: Account):
    pass

@app.post("/accounts/{cbu}")
def modify_account_balance(PostAmount: PostAmount, cbu: str = Path(..., regex=CBU_REGEX)):
    pass

#-----------------------------GET-----------------------------
@app.get("/accounts")
def get_all_accounts():
    pass

@app.get("/accounts/{cbu}")
def get_account(cbu: str = Path(..., regex=CBU_REGEX)):
    pass

#-----------------------------PUT-----------------------------
@app.put("/account/{cbu}")
def link_afk_key_to_account(cbu: str = Path(..., regex=CBU_REGEX)):
    pass

#-----------------------------DELETE-----------------------------
@app.delete("/accounts/{cbu}")
def delete_account(cbu: str = Path(..., regex=CBU_REGEX)):
    pass

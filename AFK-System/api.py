from fastapi import FastAPI, Path, HTTPException
from models import *
from postgre_utils import *
from mongo_utils import *

app = FastAPI()

#-----------------------------POST-----------------------------

@app.post("/users")
def create_user(user: User):
    pass

@app.post("/financialEntities")
def create_financial_entity(financialEntity: FinancialEntity):
    pass

@app.post("/keys/{user_id}")
def create_key(keys: AFK_Key, user_id: int= Path(..., ge=1)):
    pass

@app.post("/users/{user_id}/transaction")
def create_transaction(transaction: Transaction, user_id: int= Path(..., ge=1)):
    pass

#-----------------------------GET-----------------------------
@app.get("/users/{user_id}")
def get_user(user_id: int= Path(..., ge=1)):
    pass

@app.get("/keys/{AFK_key}")
def get_key(AFK_key: str):
    pass

@app.get("/financialEntities/{financial_id}")
def get_financial_entity(financial_id: int= Path(..., ge=1)):
    pass

@app.get("/users/{user_id}/transaction")
def get_user_transactions(user_id: int= Path(..., ge=1)):
    pass

#-----------------------------PUT-----------------------------
@app.put("/users/{user_id}")
def edit_user(user_id: int= Path(..., ge=1)):
    pass

@app.put("/financialEntities/{financial_id}")
def edit_financial_entity(financial_id: int= Path(..., ge=1)):
    pass

#-----------------------------DELETE-----------------------------
@app.delete("/users/{user_id}")
def delete_user(user_id: int= Path(..., ge=1)):
    pass

@app.delete("/financialEntities/{financial_id}")
def delete_financial_entity(financial_id: int= Path(..., ge=1)):
    pass
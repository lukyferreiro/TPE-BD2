from fastapi import FastAPI, Path, HTTPException
from models import *
from postgre_utils import *
from mongo_utils import *
import hashlib
from functools import reduce

app = FastAPI()

#-----------------------------POST-----------------------------

@app.post("/users")
def create_user(user: User):
    query = "SELECT COUNT(*) FROM users WHERE email = %(email)s"
    cursor.execute(query, {"email": user.email})
    result = cursor.fetchone()[0]
    if result == 0:
        raise HTTPException(status_code=409, detail="User already registered")

    query = "INSERT INTO users (name, password, email, isBusiness) VALUES (%(name)s, %(password)s, %(email)s, %(isBusiness)s)"
    values = {"name": user.name, "password": hashlib.sha256(user.password.encode()).hexdigest(),
              "email": user.email, "isBusiness": user.isBusiness}
    cursor.execute(query, values)
    connection.commit()
    return {}

@app.post("/financialEntities")
def create_financial_entity(financialEntity: FinancialEntity):
    query = "INSERT INTO financial_entity (apiLink) VALUES (%(apiLink)s)"
    values = {"apiLink": financialEntity.apiLink}
    cursor.execute(query, values)
    userId = cursor.fetchone()[0] 
    connection.commit()
    return {"userId": userId}

@app.post("/keys/{user_id}")
def create_key(key: AFK_Key, user_id: int= Path(..., ge=1)):
    query = "SELECT COUNT(*) FROM afk_keys WHERE financialEntityId = %(financialEntityId)s"
    cursor.execute(query, {"financialEntityId": key.financialEntityId})
    result = cursor.fetchone()[0]
    if result == 0:
        raise HTTPException(status_code=404, detail="Financial entity not found")

    #TODO chequear si el usuario es bussines y ver cuantas claves puede crear

    query = "INSERT INTO afk_keys (keyValue, keyType, userId, financialEntityId) VALUES (%(keyValue)s, %(keyType)s, %(userId)s, %(financialEntityId)s)"
    values = {"keyValue": key.keyValue, "keyType": key.keyType, "userId": user_id, "financialEntityId": key.financialEntityId}
    cursor.execute(query, values)
    connection.commit()
    return {}

@app.post("/users/{user_id}/transaction")
def create_transaction(transaction: Transaction, user_id: int= Path(..., ge=1)):
    if (transaction.amount < 0):
        raise HTTPException(status_code=400, detail="Transfer amounts have to be positive")
    pass

#-----------------------------GET-----------------------------
@app.get("/users/{user_id}")
def get_user(user_id: int= Path(..., ge=1)):
    query = "SELECT * FROM users LEFT OUTER JOIN afk_keys ON users.id = afk_keys.userId WHERE id = %(user_id)s"
    cursor.execute(query, {"user_id": user_id})
    result = cursor.fetchone()
    
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")

    user = {
        "id": result[0],
        "name": result[1],
        "email": result[3],
        "isBusiness": result[4]
    }

    #TODO ver como devolver tambien las keys que tiene asociadas

    return user

@app.get("/keys/{AFK_key}")
def get_key(AFK_key: str):
    query = "SELECT (keyValue, keyType, userId, financialEntityId) FROM afk_keys WHERE keyValue = %(AFK_key)s"
    cursor.execute(query, {"AFK_key": AFK_key})
    result = cursor.fetchone()
    
    if result is None:
        raise HTTPException(status_code=404, detail="Key not found")

    return {
        "keyValue": result[0],
        "keyType": result[1],
        "userId": result[3],
        "financialEntityId": result[4]
    }

@app.get("/financialEntities/{financial_id}")
def get_financial_entity(financial_id: int= Path(..., ge=1)):
    query = "SELECT * FROM financial_entity WHERE id = %(financial_id)s"
    cursor.execute(query, {"financial_id": financial_id})
    result = cursor.fetchone()
    
    if result is None:
        raise HTTPException(status_code=404, detail="Financial entity not found")

    return {
        "id": result[0],
        "apiLink": result[1],
    }

@app.get("/users/{user_id}/transaction")
def get_user_transactions(user_id: int= Path(..., ge=1)):
    transactions = collection.find({"userId_from": user_id})
    if transactions is None:
        HTTPException(status_code=404, detail="This user has not make any transaction")
    return {"transactions": transactions}

#-----------------------------PUT-----------------------------
@app.put("/users/{user_id}")
def edit_user(userInfo: EditUser, user_id: int= Path(..., ge=1)):
    query = "SELECT COUNT(*) FROM users WHERE id = %(user_id)s"
    cursor.execute(query, {"user_id": user_id})
    result = cursor.fetchone()[0]
    if result == 0:
        raise HTTPException(status_code=404, detail="User not found")

    query = "UPDATE users SET name = %(name)s, isBusiness = %(isBusinnes)s  WHERE id = %(user_id)s"

    values = {"name": userInfo.name, "isBusinnes": userInfo.isBusiness}
    cursor.execute(query, values)
    connection.commit()
    return {}

@app.put("/financialEntities/{financial_id}")
def edit_financial_entity(financialEntity: FinancialEntity, financial_id: int= Path(..., ge=1)):
    query = "SELECT COUNT(*) FROM financial_entity WHERE id = %(financial_id)s"
    cursor.execute(query, {"financial_id": financial_id})
    result = cursor.fetchone()[0]
    if result == 0:
        raise HTTPException(status_code=404, detail="Financial entity not found")

    query = "UPDATE users SET apiLink = %(apiLink)s WHERE id = %(financial_id)s"

    values = {"apiLink": financialEntity.apiLink}
    cursor.execute(query, values)
    connection.commit()
    return {}

#-----------------------------DELETE-----------------------------
@app.delete("/users/{user_id}")
def delete_user(user_id: int= Path(..., ge=1)):
    query = "DELETE FROM users WHERE id = %(user_id)s"
    cursor = connection.cursor()
    cursor.execute(query, {"user_id": user_id})
    connection.commit()
    return {}

@app.delete("/financialEntities/{financial_id}")
def delete_financial_entity(financial_id: int= Path(..., ge=1)):
    query = "DELETE FROM financial_entity WHERE id = %(financial_id)s"
    cursor = connection.cursor()
    cursor.execute(query, {"financial_id": financial_id})
    connection.commit()
    return {}
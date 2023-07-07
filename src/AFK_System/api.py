from fastapi import FastAPI, Path, HTTPException
from models import *
from postgre import *
from mongoimport *
import hashlib
from functools import reduce

app = FastAPI()

def _check_user_exists(user_id: int):
    query = "SELECT (id, name, email, isBusinnes) FROM users WHERE id = %(user_id)s"
    values = {"user_id": user_id}
    cursor.execute(query, values)
    result = cursor.fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return result

def _check_financial_entity_exists(financial_id: int):
    query = "SELECT (id, name, apiLink) FROM financial_entity WHERE id = %(financial_id)s"
    values = {"financial_id": financial_id}
    cursor.execute(query, values)
    result = cursor.fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="Financial entity not found")
    return result

def _check_afk_key_exits(AFK_key: str):
    query = "SELECT (keyValue, keyType, userId, financialId) FROM afk_keys WHERE keyValue = %(AFK_key)s"
    values = {"AFK_key": AFK_key}
    cursor.execute(query, values)
    result = cursor.fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="Key not found")
    return result

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
    userId = cursor.fetchone()[0] 
    connection.commit()
    return {"userId": userId}

@app.post("/financialEntities")
def create_financial_entity(financialEntity: FinancialEntity):
    query = "INSERT INTO financial_entity (name, apiLink) VALUES (%(name)s, %(apiLink)s)"
    values = {"name": financialEntity.name ,"apiLink": financialEntity.apiLink}
    cursor.execute(query, values)
    financialId = cursor.fetchone()[0] 
    connection.commit()
    return {"financialId": financialId}

@app.post("/keys/{user_id}")
def create_key(key: AFK_Key, user_id: int = Path(..., ge=1)):
    _check_financial_entity_exists(key.financial_id)

    result = _check_user_exists(user_id)
    isBusiness = result[3]

    query = "SELECT COUNT(*) FROM afk_keys WHERE userId = %(user_id)s"
    values = {"user_id": user_id}
    cursor.execute(query, values)
    cant_keys = cursor.fetchone()[0]

    if((!isBusiness and cant_keys < 5) or (isBusiness and cant_keys < 20)):
        query = "INSERT INTO afk_keys (keyValue, keyType, userId, financialId) VALUES (%(keyValue)s, %(keyType)s, %(userId)s, %(financialId)s)"
        values = {"keyValue": key.keyValue, "keyType": key.keyType, "userId": user_id, "financialId": key.financialId}
        cursor.execute(query, values)
        connection.commit()

        #TODO llamar a la api del banco para asociar la clave a la cuenta

        return {}
    else:
        raise HTTPException(status_code=409, detail="You can not create more keys (5 for people and 20 for business)")

@app.post("/users/{user_id}/transaction")
def create_transaction(transaction: Transaction, user_id: int= Path(..., ge=1)):
    if (transaction.amount < 0):
        raise HTTPException(status_code=400, detail="Transfer amounts have to be positive")

    # TODO
    # ...

#-----------------------------GET-----------------------------

@app.get("/users/{user_id}")
def get_user(user_id: int= Path(..., ge=1)):
    query = "SELECT * FROM users LEFT OUTER JOIN afk_keys ON users.id = afk_keys.userId WHERE id = %(user_id)s"
    values = {"user_id": user_id}
    cursor.execute(query, values)
    result = cursor.fetchone()
    
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")

    user = {
        "id": result[0],
        "name": result[1],
        "email": result[2],
        "isBusiness": result[3]
    }

    #TODO ver como devolver tambien las keys que tiene asociadas

    return user

@app.get("/keys/{AFK_key}")
def get_key(AFK_key: str):
    result = _check_afk_key_exits(AFK_key)

    return {
        "keyValue": result[0],
        "keyType": result[1],
        "userId": result[2],
        "financialId": result[3]
    }

@app.get("/financialEntities/{financial_id}")
def get_financial_entity(financial_id: int= Path(..., ge=1)):
    result = _check_financial_entity_exists(financial_id)

    return {
        "id": result[0],
        "name": result[1]
        "apiLink": result[2],
    }

# TODO chequear
@app.get("/users/{user_id}/transactions")
def get_user_transactions(user_id: int= Path(..., ge=1)):
    transactions = collection.find({"userId_from": user_id})

    if transactions is None:
        HTTPException(status_code=404, detail="This user has not make any transaction")

    return {"transactions": transactions}

#-----------------------------PUT-----------------------------

@app.put("/users/{user_id}")
def edit_user(userInfo: EditUser, user_id: int= Path(..., ge=1)):
    _check_user_exists(user_id)

    query = "UPDATE users SET name = %(name)s, isBusiness = %(isBusinnes)s  WHERE id = %(user_id)s"
    values = {"name": userInfo.name, "isBusinnes": userInfo.isBusiness, "user_id": user_id}
    cursor.execute(query, values)
    connection.commit()
    return {"message": "User successfully updated"}

@app.put("/financialEntities/{financial_id}")
def edit_financial_entity(financialEntity: FinancialEntity, financial_id: int= Path(..., ge=1)):
    _check_financial_entity_exists(financial_id)

    query = "UPDATE users SET name = %(name)s, apiLink = %(apiLink)s WHERE id = %(financial_id)s"
    values = {"name": financialEntity.name, "apiLink": financialEntity.apiLink, "financial_id": financial_id}
    cursor.execute(query, values)
    connection.commit()
    return {"message": "Financial entity successfully updated"}

#-----------------------------DELETE-----------------------------

@app.delete("/users/{user_id}")
def delete_user(user_id: int= Path(..., ge=1)):
    _check_user_exists(user_id)

    query = "DELETE FROM users WHERE id = %(user_id)s"
    cursor = connection.cursor()
    values = {"user_id": user_id}
    cursor.execute(query, values)
    connection.commit()
    return {"message": "User successfully deleted"}

@app.delete("/financialEntities/{financial_id}")
def delete_financial_entity(financial_id: int= Path(..., ge=1)):
    _check_financial_entity_exists(financial_id)

    query = "DELETE FROM financial_entity WHERE id = %(financial_id)s"
    cursor = connection.cursor()
    values = {"financial_id": financial_id}
    cursor.execute(query, values)
    connection.commit()
    return {"message": "Financial entity successfully deleted"}


@app.on_event("shutdown")
async def shutdown_event():
    cursor.close()
    connection.close()
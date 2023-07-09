from fastapi import FastAPI, Path, Query, HTTPException
from models import *
from postgre_utils import *
from mongo_utils import *
import hashlib
from functools import reduce
import requests
import psycopg2
from pydantic import EmailStr, constr, Field

app = FastAPI()

def _check_user_exists(user_id: int):
    query = "SELECT userId, name, email, isBusiness FROM users WHERE userId = %(user_id)s"
    values = {"user_id": user_id}
    cursor.execute(query, values)
    result = cursor.fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return result

def _check_financial_entity_exists(financial_id: int):
    query = "SELECT financialId, name, apiLink FROM financialEntities WHERE financialId = %(financial_id)s"
    values = {"financial_id": financial_id}
    cursor.execute(query, values)
    result = cursor.fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="Financial entity not found")
    return result

def _check_afk_key_exits(afk_key: str):
    query = "SELECT value, type, userId, financialId FROM afkKeys WHERE value = %(afk_key)s"
    values = {"afk_key": afk_key}
    cursor.execute(query, values)
    result = cursor.fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="Key not found")
    return result

#-----------------------------POST-----------------------------

@app.post("/users")
def create_user(user: PostUser):
    query = "SELECT COUNT(*) FROM users WHERE email = %(email)s"
    cursor.execute(query, {"email": user.email})
    result = cursor.fetchone()[0]

    if result != 0:
        raise HTTPException(status_code=409, detail="User already registered")

    query = "INSERT INTO users (name, password, email, isBusiness) VALUES (%(name)s, %(password)s, %(email)s, %(isBusiness)s)"
    values = {"name": user.name, "password": hashlib.sha256(user.password.encode()).hexdigest(),
              "email": user.email, "isBusiness": user.isBusiness}
    cursor.execute(query, values)
    connection.commit()
    return {"message": "User successfully created"}

"""
@app.post("/financialEntities")
def create_financial_entity(financialEntity: PostFinancialEntity):
    query = "INSERT INTO financialEntities (financialId, name, apiLink) VALUES (%(id)s, %(name)s, %(apiLink)s)"
    values = {"id": financialEntity.financialId, "name": financialEntity.name ,"apiLink": financialEntity.apiLink}
    cursor.execute(query, values)
    connection.commit()
    return {"message": "Financial entity successfully created"}
"""

@app.post("/keys")
def create_key(afkKey: PostAfkKey, user_id: int = Query(..., ge=1)):
    result_finacial_entity = _check_financial_entity_exists(afkKey.cbu[:7])

    print(result_finacial_entity)

    #TODO chequear que el CBU exista en el banco
    #...

    result_user = _check_user_exists(user_id)
    isBusiness = bool(result_user[3])

    query = "SELECT COUNT(*) FROM afkKeys WHERE userId = %(user_id)s"
    values = {"user_id": user_id}

    cursor = connection.cursor()

    cursor.execute(query, values)
    cant_keys = cursor.fetchone()[0]

    if((not isBusiness and cant_keys < 5) or (isBusiness and cant_keys < 20)):
        query = "INSERT INTO afkKeys (value, type, userId, financialId) VALUES (%(value)s, %(type)s, %(userId)s, %(financialId)s)"
        values = {"value": afkKey.value, "type": afkKey.keyType, "userId": user_id, "financialId": result_finacial_entity[0]}
        cursor.execute(query, values)
        connection.commit()

        url = f"{result_finacial_entity[2]}accounts/account/link"
        print(url)
        body = {
            'afk_key': afkKey.value,
            'cbu': afkKey.cbu
        }
        print(body)
        headers = {
            'accept': application/json,
            'Content-Type': application/json
        }
        response = requests.put(url, json=body, headers=headers)
        print(response)
        print(response.status_code)

        if response.status_code >= 400:
            # Rollbackeamos si falla el pedido al banco
            query = "DELETE FROM afkKeys WHERE value = %(value)s"
            cursor = connection.cursor()
            values = {"value": value}
            cursor.execute(query, values)
            connection.commit()

            raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])

        return {"message": "AFK key successfully created"}
    else:
        raise HTTPException(status_code=409, detail="You can not create more keys (5 for people and 20 for business)")

@app.post("/users/{user_id}/transaction")
def create_transaction(postTransaction: PostTransaction, user_id: int= Path(..., ge=1)):
    if (postTransaction.amount < 0):
        raise HTTPException(status_code=400, detail="Transfer amounts have to be positive")

    # TODO
    # ...

#-----------------------------GET-----------------------------

# Endpoint para obtener todas las cuentas
@app.get("/users")
def get_all_users():
    query = "SELECT userId, name, email, isBusiness FROM users"
    cursor.execute(query)
    result = cursor.fetchall()

    if result is None:
        raise HTTPException(status_code=404, detail="No users found")

    users = []
    print(result)
    for row in result:
        user = {
            "userId": row[0],
            "name": row[1],
            "email": row[2],
            "isBusiness": row[3]
        }
        users.append(user)

    return users

# Endpoint para obtener todas las cuentas
@app.get("/financialEntities")
def get_all_financial_entities():
    query = "SELECT financialId, name, apiLink FROM financialEntities"
    cursor.execute(query)
    result = cursor.fetchall()

    if result is None:
        raise HTTPException(status_code=404, detail="No financial entity found")

    financial_entities = []
    print(result)
    for row in result:
        account = {
            "financialId": row[0],
            "name": row[1],
            "apiLink": row[2],
        }
        financial_entities.append(account)

    return financial_entities

@app.get("/users/{user_id}")
def get_user(user_id: int = Path(..., ge=1)):
    query = """
        SELECT users.userId, users.name, users.email, users.isBusiness, afkKeys.keyId, afkKeys.value, afkKeys.type
        FROM users
        LEFT JOIN afkKeys ON users.userId = afkKeys.userId
        WHERE users.userId = %(user_id)s
    """
    values = {"user_id": user_id}
    cursor.execute(query, values)
    results = cursor.fetchall()

    if len(results) == 0:
        raise HTTPException(status_code=404, detail="User not found")

    print(results)

    user = {
        "userId": results[0][0],
        "name": results[0][1],
        "email": results[0][2],
        "isBusiness": results[0][3],
        "keys": []
    }

    for row in results:
        if row[4] is not None:
            key = {
                "keyId": row[4],
                "value": row[5],
                "type": row[6]
            }
            user["keys"].append(key)

    return user

@app.get("/keys/{afk_key}")
def get_key(afk_key: str = Path(...)):
    result = _check_afk_key_exits(afk_key)

    return {
        "value": result[0],
        "type": result[1],
        "userId": result[2],
        "financialId": result[3]
    }

@app.get("/financialEntities/{financial_id}")
def get_financial_entity(financial_id: int= Path(..., ge=1)):
    result = _check_financial_entity_exists(financial_id)

    return {
        "id": result[0],
        "name": result[1],
        "apiLink": result[2]
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
def edit_user(putUser: PutUser, user_id: int= Path(..., ge=1)):
    _check_user_exists(user_id)

    query = "UPDATE users SET name = %(name)s, isBusiness = %(isBusiness)s  WHERE userId = %(user_id)s"
    values = {"name": putUser.name, "isBusiness": putUser.isBusiness, "user_id": user_id}
    cursor.execute(query, values)
    connection.commit()
    return {"message": "User successfully updated"}

#-----------------------------DELETE-----------------------------

@app.delete("/users/{user_id}")
def delete_user(user_id: int= Path(..., ge=1)):
    _check_user_exists(user_id)

    query = "DELETE FROM users WHERE userId = %(user_id)s"
    cursor = connection.cursor()
    values = {"user_id": user_id}
    cursor.execute(query, values)
    connection.commit()
    return {"message": "User successfully deleted"}

"""
@app.delete("/financialEntities/{financial_id}")
def delete_financial_entity(financial_id: int= Path(..., ge=1)):
    _check_financial_entity_exists(financial_id)

    query = "DELETE FROM financialEntities WHERE financialId = %(financial_id)s"
    cursor = connection.cursor()
    values = {"financial_id": financial_id}
    cursor.execute(query, values)
    connection.commit()
    return {"message": "Financial entity successfully deleted"}
"""    

@app.delete("/keys/{afk_key}")
def delete_afk_key(afk_key: str = Path(...)):
    result_key = _check_afk_key_exits(afk_key)
    result_financial_entity = _check_financial_entity_exists(result_key[3])

    url = f"{result_financial_entity[2]}/accounts/account/unlink"
    print(url)
    body = {
        "afk_key": afk_key,
    }
    response = requests.put(url=url, json=body)

    if response.status_code == 200:
        #Si se pudo desvincular en el banco, borramos la clave
        query = "DELETE FROM afkKeys WHERE value = %(afk_key)s"
        cursor = connection.cursor()
        values = {"afk_key": afk_key}
        cursor.execute(query, values)
        connection.commit()
        return {"message": "AFK key successfully deleted"}
    else:
        raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])    


@app.on_event("shutdown")
async def shutdown_event():
    cursor.close()
    connection.close()
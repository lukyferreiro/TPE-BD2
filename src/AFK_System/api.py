from fastapi import FastAPI, Path, Query, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from models import PostUser, PostFinancialEntity, PostAfkKey, PostTransaction, PutUser
from postgre_utils import connection, cursor
from mongo_utils import client, db, collection
from api_utils import _check_user_exists, _check_user_exists_by_email, _check_financial_entity_exists, _check_afk_key_exists, _check_relation_user_key, _get_api_link_from_afk_key, _validate_credentials, _unlink_key_from_account, _delete_user_from_id
import hashlib
import requests
import psycopg2
from pydantic import EmailStr, constr, Field
from datetime import datetime
import pytz


app = FastAPI()
security = HTTPBasic()

#-----------------------------POST-----------------------------

@app.post("/users")
def create_user(user: PostUser):
    query = "SELECT COUNT(*) FROM users WHERE email = %(email)s"
    values = {"email": user.email}
    cursor.execute(query, values)
    result = cursor.fetchone()[0]

    if result != 0:
        raise HTTPException(status_code=409, detail="User already registered")

    query = "INSERT INTO users (name, password, email, isBusiness) VALUES (%(name)s, %(password)s, %(email)s, %(isBusiness)s)"
    values = {"name": user.name, "password": hashlib.sha256(user.password.encode()).hexdigest(),
              "email": user.email, "isBusiness": user.isBusiness}
    cursor.execute(query, values)
    connection.commit()
    return {"message": "User created successfully"}

"""
@app.post("/financialEntities")
def create_financial_entity(financialEntity: PostFinancialEntity):
    query = "INSERT INTO financialEntities (financialId, name, apiLink) VALUES (%(id)s, %(name)s, %(apiLink)s)"
    values = {"id": financialEntity.financialId, "name": financialEntity.name ,"apiLink": financialEntity.apiLink}
    cursor.execute(query, values)
    connection.commit()
    return {"message": "Financial entity created successfully"}
"""

@app.post("/keys")
def create_key(afkKey: PostAfkKey, credentials: HTTPBasicCredentials = Depends(security)):

    result_finacial_entity = _check_financial_entity_exists(afkKey.cbu[:7])

    email = credentials.username
    password = credentials.password
    user_id, isBusiness = _validate_credentials(email, password)

    query = "SELECT COUNT(*) FROM afkKeys WHERE userId = %(user_id)s"
    values = {"user_id": user_id}

    cursor.execute(query, values)
    cant_keys = cursor.fetchone()[0]

    if((not isBusiness and cant_keys < 5) or (isBusiness and cant_keys < 20)):
        query = "INSERT INTO afkKeys (value, type, userId, financialId) VALUES (%(value)s, %(type)s, %(userId)s, %(financialId)s)"
        values = {"value": afkKey.value, "type": afkKey.keyType, "userId": user_id, "financialId": result_finacial_entity[0]}
        cursor.execute(query, values)
        connection.commit()

        url = f"{result_finacial_entity[2]}/accounts/account/link"
        body = {
            'afk_key': f"{afkKey.value}",
            'cbu': f"{afkKey.cbu}"
        }

        try:
            response = requests.put(url, json=body)
        except requests.exceptions.RequestException as e:
            # Rollbackeamos si falla el pedido al banco
            query = "DELETE FROM afkKeys WHERE value = %(value)s"
            values = {"value": afkKey.value}
            cursor.execute(query, values)
            connection.commit()
            raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])
        
        return {"message": "AFK key created successfully"}

    else:
        raise HTTPException(status_code=409, detail="You can not create more keys (5 for people and 20 for business)")

@app.post("/users/transactions")
def create_transaction(postTransaction: PostTransaction, credentials: HTTPBasicCredentials = Depends(security)):
    email = credentials.username
    password = credentials.password
    user_id_from, _ = _validate_credentials(email, password)

    if (postTransaction.amount < 0):
        raise HTTPException(status_code=400, detail="Transfer amounts have to be positive")

    apiLink_from = _get_api_link_from_afk_key(postTransaction.afk_key_from, "from")
    apiLink_to = _get_api_link_from_afk_key(postTransaction.afk_key_to, "to")
    
    url_from = f"{apiLink_from[2]}/accounts/account"
    body_from = {
        'afk_key': f"{apiLink_from}",
        'amount': float(-postTransaction.amount)
    }
    response_from = requests.post(url_from, json=body_from)

    if response_from.status_code == 200:
        url_from = f"{apiLink_to[2]}/accounts/account"
        body_to = {
            'afk_key': f"{apiLink_to}",
            'amount': float(postTransaction.amount)
        }
        response_to = requests.post(url_from, json=body_to)

        if response_to.status_code == 200:
            # TODO guardar toda la info en Mongo
            argentina_tz = pytz.timezone('America/Argentina/Buenos_Aires')
            current_datetime = datetime.now()
            current_datetime = current_datetime.astimezone(argentina_tz)
            formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

            transaction_data = {
                "to": postTransaction.afk_key_to,
                "from": postTransaction.afk_key_to,
                "amount": 100.0,
                "date": formatted_datetime,
                "user_id": user_id_from
            }       
            result = collection.insert_one(transaction_data)
            if result.inserted_id:
                print("Transacción insertada con éxito. ObjectID:", result.inserted_id)
            else:
                print("Error al insertar la transacción.")

            return {"message": "Transaction completed successfully"}
        else: 
            # Si falla la segunda transacción, le devuelvo al primer usuario su dinero
            url_from = f"{apiLink_from[2]}/accounts/account"
            body_from = {
                'afk_key': f"{apiLink_from}",
                'amount': float(postTransaction.amount)
            }
            response_from = requests.post(url_from, json=body_from)
            pass

    else :
        # TODO ver que se hace. Enviar mensaje de que transacción falló
        pass


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

# Endpoint para obtener un usuario a partir de su ID
@app.get("/users/{user_id}")
def get_user(user_id: int = Path(..., ge=1)):
    query = """
        SELECT users.userId, users.name, users.email, users.isBusiness, afkKeys.value, afkKeys.type
        FROM users LEFT JOIN afkKeys ON users.userId = afkKeys.userId WHERE users.userId = %(user_id)s
    """
    values = {"user_id": user_id}
    cursor.execute(query, values)
    results = cursor.fetchall()

    if len(results) == 0:
        raise HTTPException(status_code=404, detail="User not found")

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
                "value": row[4],
                "type": row[5]
            }
            user["keys"].append(key)

    return user

# Endpoint para obtener el balance de un usuario a partir de su AFK key
@app.get("/users/balance/{afk_key}")
def get_balance(afk_key: str = Path(..., min_length=1), credentials: HTTPBasicCredentials = Depends(security)):
    email = credentials.username
    password = credentials.password
    _validate_credentials(email, password)

    result_key = _check_afk_key_exists(afk_key)
    result_finacial_entity = _check_financial_entity_exists(result_key[3])

    url = f"{result_finacial_entity[2]}/accounts/account/balance"
    params = {'afk_key': afk_key}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status() 
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail="Error al procesar la solicitud")

    return {"balance": float(response.json()['balance'])}

@app.get("/keys/{afk_key}")
def get_key(afk_key: str = Path(...)):
    result = _check_afk_key_exists(afk_key)

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
@app.get("/users/transactions")
def get_user_transactions(credentials: HTTPBasicCredentials = Depends(security)):
    email = credentials.username
    password = credentials.password
    user_id, _ = _validate_credentials(email, password)

    transactions = collection.find({"userId_from": user_id})

    if transactions is None:
        HTTPException(status_code=404, detail="This user has not made any transactions yet")

    return {"transactions": transactions}

#-----------------------------PUT-----------------------------

@app.put("/users")
def edit_user(putUser: PutUser, credentials: HTTPBasicCredentials = Depends(security)):
    email = credentials.username
    password = credentials.password
    user_id, _ = _validate_credentials(email, password)

    query = "UPDATE users SET name = %(name)s, isBusiness = %(isBusiness)s  WHERE userId = %(user_id)s"
    values = {"name": putUser.name, "isBusiness": putUser.isBusiness, "user_id": user_id}
    cursor.execute(query, values)
    connection.commit()
    return {"message": "User updated successfully"}

#-----------------------------DELETE-----------------------------

@app.delete("/users/{user_id}")
def delete_user(user_id: int= Path(..., ge=1)):
    _check_user_exists(user_id)

    query = """
        SELECT afkKeys.value, financialEntities.apiLink
        FROM (users JOIN afkKeys ON users.userId = afkKeys.userId) JOIN financialEntities ON afkKeys.financialId = financialEntities.apiLink
        WHERE users.userId = %(user_id)s
    """
    values = {"user_id": user_id}
    cursor.execute(query, values)
    results = cursor.fetchall()

    if results is None:
        _delete_user_from_id(user_id)
        return {"message": "User deleted successfully"}
    else :
        # Al borrar el usuario, primero desvinculamos todas las claves de sus bancos
        for row in results:
            response = _unlink_key_from_account(row[1], row[0])
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Error while unlinking '{row[0]}' AFK key from '{row[1]}' entity")
                
            # TODO habria que rollbackear si falla algun unlink de la clave
            
        _delete_user_from_id(user_id)
        return {"message": "User deleted successfully"}

"""
@app.delete("/financialEntities/{financial_id}")
def delete_financial_entity(financial_id: int= Path(..., ge=1)):
    _check_financial_entity_exists(financial_id)

    query = "DELETE FROM financialEntities WHERE financialId = %(financial_id)s"
    values = {"financial_id": financial_id}
    cursor.execute(query, values)
    connection.commit()
    return {"message": "Financial entity deleted successfully"}
"""    

@app.delete("/keys/{afk_key}")
def delete_afk_key(afk_key: str = Path(...), credentials: HTTPBasicCredentials = Depends(security)):
    email = credentials.username
    password = credentials.password
    user_id, _ = _validate_credentials(email, password)
    result_key = _check_afk_key_exists(afk_key)
    result_financial_entity = _check_financial_entity_exists(result_key[3])

    # Chequeamos que la clave le pertenezca al usuario que se autentica
    _check_relation_user_key(user_id, afk_key)

    response = _unlink_key_from_account(result_financial_entity[2], afk_key)

    if response.status_code == 200:
        #Si se pudo desvincular en el banco, borramos la clave
        query = "DELETE FROM afkKeys WHERE value = %(afk_key)s"
        values = {"afk_key": afk_key}
        cursor.execute(query, values)
        connection.commit()
        return {"message": "AFK key deleted successfully"}

@app.on_event("shutdown")
async def shutdown_event():
    #cursor.close()
    connection.close()
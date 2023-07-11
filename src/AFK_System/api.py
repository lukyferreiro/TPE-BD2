from fastapi import FastAPI, Path, Query, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from models import PostUser, PostAfkKey, PostTransaction, PutUser
from postgre_utils import connection, cursor
from mongo_utils import collection
from api_utils import _check_user_exists, _check_user_exists_by_email, _check_financial_entity_exists, _check_afk_key_exists, _check_relation_user_key, _get_api_link_from_afk_key, _validate_credentials, _delete_user_from_id, _delete_afk_key
from bank_utils import _unlink_key_from_account, _link_key_from_account, _get_balance_from_account, _make_transaction
import hashlib

app = FastAPI()
security = HTTPBasic()

#-----------------------------POST-----------------------------

@app.post("/users")
def create_user(user: PostUser):
    """Endpoint para registrar un nuevo usuario"""

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
    """Endpoint para registrar una nueva clave"""

    result_financial_entity = _check_financial_entity_exists(afkKey.cbu[:7])

    email = credentials.username
    password = credentials.password
    user_id, isBusiness = _validate_credentials(email, password)

    query = "SELECT COUNT(*) FROM afkKeys WHERE userId = %(user_id)s"
    values = {"user_id": user_id}

    cursor.execute(query, values)
    cant_keys = cursor.fetchone()[0]

    if((not isBusiness and cant_keys < 5) or (isBusiness and cant_keys < 20)):
        query = "INSERT INTO afkKeys (value, userId, financialId) VALUES (%(value)s, %(userId)s, %(financialId)s)"
        values = {"value": afkKey.value, "userId": user_id, "financialId": result_financial_entity[0]}
        cursor.execute(query, values)
        connection.commit()

        response = _link_key_from_account(result_financial_entity[2], afkKey.value, afkKey.cbu)
        
        return {"message": response.json()['message']}

    else:
        raise HTTPException(status_code=409, detail="You can not create more keys (5 for people and 20 for business)")

@app.post("/user/transactions")
def create_transaction(postTransaction: PostTransaction, credentials: HTTPBasicCredentials = Depends(security)):
    """Endpoint para crear una transaccion"""

    if (postTransaction.amount < 0):
        raise HTTPException(status_code=400, detail="Transfer amounts have to be positive")

    if (postTransaction.afk_key_from == postTransaction.afk_key_to):
        raise HTTPException(status_code=409, detail="Can not make transactions to the same account")

    email = credentials.username
    password = credentials.password
    user_id_from, _ = _validate_credentials(email, password)

    # Chequeamos que la clave le pertenezca al usuario que se autentica
    _check_relation_user_key(user_id_from, postTransaction.afk_key_from)

    apiLink_from = _get_api_link_from_afk_key(postTransaction.afk_key_from, "from")
    apiLink_to = _get_api_link_from_afk_key(postTransaction.afk_key_to, "to")

    _make_transaction(apiLink_from, apiLink_to, postTransaction.amount,
                      postTransaction.afk_key_from, postTransaction.afk_key_to,
                      user_id_from)

    return {"message": "Transaction completed successfully"}


#-----------------------------GET-----------------------------

@app.get("/users")
def get_all_users():
    """Endpoint para obtener todos los usuarios"""

    query = "SELECT userId, name, email, isBusiness FROM users"
    cursor.execute(query)
    result = cursor.fetchall()

    if result is None:
        raise HTTPException(status_code=404, detail="No users found")

    users = []
    for row in result:
        user = {
            "userId": row[0],
            "name": row[1],
            "email": row[2],
            "isBusiness": row[3]
        }
        users.append(user)

    return users

@app.get("/financialEntities")
def get_all_financial_entities():
    """Endpoint para obtener todas las entidades financieras"""

    query = "SELECT financialId, name, apiLink FROM financialEntities"
    cursor.execute(query)
    result = cursor.fetchall()

    if result is None:
        raise HTTPException(status_code=404, detail="No financial entity found")

    financial_entities = []
    for row in result:
        account = {
            "financialId": row[0],
            "name": row[1],
            "apiLink": row[2],
        }
        financial_entities.append(account)

    return financial_entities

@app.get("/users/{user_id}")
def get_user(user_id: int = Path(..., title="User ID", ge=1)):
    """Endpoint para obtener un usuario a partir de su ID"""

    query = """
        SELECT users.userId, users.name, users.email, users.isBusiness, afkKeys.value
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
            }
            user["keys"].append(key)

    return user

@app.get("/user")
def get_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Endpoint para obtener un usuario a partir de sus credenciales"""

    print(credentials.username)
    print(credentials.password)

    email = credentials.username
    password = credentials.password
    user_id, _ = _validate_credentials(email, password)

    query = """
        SELECT users.userId, users.name, users.email, users.isBusiness, afkKeys.value, afkKeys.financialId
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
                "financialId": row[5]
            }
            user["keys"].append(key)

    return user

@app.get("/user/balance")
def get_balance(afk_key: str = Query(..., title="AFK key", min_length=1), credentials: HTTPBasicCredentials = Depends(security)):
    """Endpoint para obtener el balance de un usuario a partir de su AFK key"""
    
    email = credentials.username
    password = credentials.password
    _validate_credentials(email, password)

    result_key = _check_afk_key_exists(afk_key)
    result_financial_entity = _check_financial_entity_exists(result_key[2])

    response = _get_balance_from_account(result_financial_entity[2], afk_key)

    return {"balance": float(response.json()['balance'])}

@app.get("/keys")
def get_key(afk_key: str = Query(..., title="AFK key", min_length=1), credentials: HTTPBasicCredentials = Depends(security)):
    """Endpoint que devuelve una clave AFK a partir de su valor"""
    email = credentials.username
    password = credentials.password
    user_id, _ = _validate_credentials(email, password)
    result = _check_afk_key_exists(afk_key)
    _check_relation_user_key(user_id, afk_key)

    return {
        "value": result[0],
        "userId": result[1],
        "financialId": result[2]
    }

@app.get("/financialEntities/{financial_id}")
def get_financial_entity(financial_id: str= Path(..., title="Financial Entity ID")):
    """Endpoint que devuelve una entidad financiera a partir de su ID"""
    
    result = _check_financial_entity_exists(financial_id)

    return {
        "id": result[0],
        "name": result[1],
        "apiLink": result[2]
    }

@app.get("/user/transactions")
def get_user_transactions(credentials: HTTPBasicCredentials = Depends(security)):
    """Endpoint que devuelve todas las transacciones de un usuario"""
    
    email = credentials.username
    password = credentials.password
    user_id_credentials, _ = _validate_credentials(email, password)

    try:
        transactions = list(collection.find({"userId_from": user_id_credentials}))
    except pymongo.errors.PyMongoError as e:
        raise HTTPException(status_code=500, detail="Could not retrieve transactions. Try again later")

    if transactions is None:
        raise HTTPException(status_code=404, detail="This user has not made any transactions yet")

    # TODO: with afk_key_to bring some user info
    for transaction in transactions:
        transaction["_id"] = str(transaction["_id"])

    return {"transactions": transactions}

#-----------------------------PUT-----------------------------

@app.put("/user")
def edit_user(putUser: PutUser, credentials: HTTPBasicCredentials = Depends(security)):
    """Endpoint para editar la informacion de un usuario"""

    email = credentials.username
    password = credentials.password
    user_id, _ = _validate_credentials(email, password)

    query = "UPDATE users SET name = %(name)s WHERE userId = %(user_id)s"
    values = {"name": putUser.name, "user_id": user_id}
    cursor.execute(query, values)
    connection.commit()
    return {"message": "User updated successfully"}

#-----------------------------DELETE-----------------------------

"""
@app.delete("/users/{user_id}")
def delete_user(user_id: int= Path(..., ge=1)):
    _check_user_exists(user_id)

    query = ""
        SELECT afkKeys.value, financialEntities.apiLink
        FROM (users JOIN afkKeys ON users.userId = afkKeys.userId) JOIN financialEntities ON afkKeys.financialId = financialEntities.apiLink
        WHERE users.userId = %(user_id)s
    ""
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
 
@app.delete("/keys")
def delete_afk_key(afk_key: str = Query(..., title="AFK key", min_length=1), credentials: HTTPBasicCredentials = Depends(security)):
    """Endpoint para eliminar una clave AFK"""
    
    email = credentials.username
    password = credentials.password
    user_id, _ = _validate_credentials(email, password)
    result_key = _check_afk_key_exists(afk_key)
    result_financial_entity = _check_financial_entity_exists(result_key[2])

    # Chequeamos que la clave le pertenezca al usuario que se autentica
    _check_relation_user_key(user_id, afk_key)

    response = _unlink_key_from_account(result_financial_entity[2], afk_key)

    if response.status_code == 200:
        #Si se pudo desvincular en el banco, borramos la clave
        _delete_afk_key(afk_key)
        return {"message": response.json()['message']}

@app.on_event("shutdown")
async def shutdown_event():
    cursor.close()
    connection.close()
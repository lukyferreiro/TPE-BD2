from fastapi import FastAPI, Path, Query, HTTPException
from models import PostAmount, PutLink, PutUnlink
from api_utils import _check_account_exists_by_cbu, _check_account_exists_by_key
import random

#TODO: modify according to chosen bank
from bank1_config import connection, cursor


app = FastAPI()

"""
Un CBU esta formado por 22 digitos donde:
-- Los primeros 3 son el codigo del banco
-- Los siguientes 4 son el codigo de sucursal
-- Los ultimos 15 son el numero de cuenta
"""

#-----------------------------POST-----------------------------

"""
# Endpoint para crear una cuenta
@app.post("/accounts")
def create_account(username: str):
    CBU = _create_cbu()
    query = "INSERT INTO accounts (cbu, username, balance) VALUES (%(cbu)s, %(username)s, %(balance)s)"
    values = {"cbu": CBU, "username": username, "balance": 0.0}
    cursor.execute(query, values)
    connection.commit()
    return {"cbu": CBU}
"""

@app.post("/accounts/account")
def modify_account_balance(postAmount: PostAmount):
    """Endpoint para modificar el saldo de una cuenta"""

    result = _check_account_exists_by_key(postAmount.afk_key)
    
    new_balance = float(result[2])
    new_balance += postAmount.amount

    if new_balance < 0:
        raise HTTPException(status_code=403, detail="Insufficient funds")

    query = "UPDATE accounts SET balance = %(balance)s WHERE afk_key = %(afk_key)s"
    values = {"balance": new_balance, "afk_key": postAmount.afk_key}
    cursor.execute(query, values)
    connection.commit()
    return {"balance": new_balance}

#-----------------------------GET-----------------------------

@app.get("/accounts")
def get_all_accounts():
    """Endpoint que devuelve todas las cuentas"""
    
    query = "SELECT cbu, username, balance, afk_key FROM accounts"
    cursor.execute(query)
    result = cursor.fetchall()

    if result is None:
        raise HTTPException(status_code=404, detail="No accounts found")

    accounts = []
    for row in result:
        account = {
            "cbu": row[0],
            "username": row[1],
            "balance": row[2],
            "afk_key": row[3]
        }
        accounts.append(account)

    return accounts

    
"""
# Endpoint para obtener una cuenta específica
@app.get("/accounts/account/{cbu}")
def get_account(cbu: str = Path(..., title="CBU", regex=CBU_REGEX)):
    result = _check_account_exists_by_cbu(cbu)

    return {
        "cbu": result[0],
        "username": result[1],
        "balance": result[2],
        "afk_key": result[3]
    }
"""

@app.get("/accounts/account/balance")
def get_balance(afk_key: str = Query(..., title="AFK key", min_length=1)):
    """Endpoint que devuelve una cuenta a partir de una clave AFK"""
    
    result = _check_account_exists_by_key(afk_key)
    return {"balance": result[2]}

#-----------------------------PUT-----------------------------

@app.put("/accounts/account/link")
def link_afk_key_to_account(putLink: PutLink):
    """Endpoint para vincular una clave AFK a una cuenta"""
    
    _check_account_exists_by_cbu(putLink.cbu)

    query = "SELECT COUNT(*) FROM accounts WHERE afk_key = %(afk_key)s"
    values = {"afk_key": putLink.afk_key}
    cursor.execute(query, values)
    result = cursor.fetchone()[0]

    if result != 0:
        raise HTTPException(status_code=409, detail="AFK key already linked")

    query = "SELECT afk_key FROM accounts WHERE cbu = %(cbu)s"
    values = {"cbu": putLink.cbu}
    cursor.execute(query, values)
    result = cursor.fetchone()[0]

    if result != None:
        raise HTTPException(status_code=409, detail="Account already has an AFK key linked")

    query = "UPDATE accounts SET afk_key = %(afk_key)s WHERE cbu = %(cbu)s"
    values = {"afk_key": putLink.afk_key, "cbu": putLink.cbu}
    cursor.execute(query, values)
    connection.commit()
    return {"message": "AFK key linked successfully"}

@app.put("/accounts/account/unlink")
def unlink_afk_key_to_account(putUnlink: PutUnlink):
    """Endpoint para desvincular una clave AFK a una cuenta"""
    
    _check_account_exists_by_key(putUnlink.afk_key)

    query = "UPDATE accounts SET afk_key = %(afk_key_to_set)s WHERE afk_key = %(afk_key)s"
    values = {"afk_key_to_set": None, "afk_key": putUnlink.afk_key}
    cursor.execute(query, values)
    connection.commit()
    return {"message": "AFK key unlinked successfully"}


#-----------------------------DELETE-----------------------------

"""
# Endpoint para eliminar una cuenta
@app.delete("/accounts/account/{cbu}")
def delete_account(cbu: str = Path(..., title="CBU", regex=CBU_REGEX)):
    _check_account_exists_by_cbu(cbu)

    query = "DELETE FROM accounts WHERE cbu = %(cbu)s"
    cursor.execute(query, {"cbu": cbu})
    connection.commit()
    return {"message": "Account deleted successfully"}
"""

@app.on_event("shutdown")
async def shutdown_event():
    cursor.close()
    connection.close()
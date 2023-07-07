from fastapi import FastAPI, Path, HTTPException, Query
from postgre_utils import *
import random
from typing import Optional

app = FastAPI()

"""
Un CBU esta formado por 22 digitos donde:
-- Los primeros 3 son el codigo del banco
-- Los siguientes 4 son el codigo de sucursal
-- Los ultimos 15 son el numero de cuenta
"""
CBU_PREFIX = "1111111"
CBU_SUFFIX_LEN = 15
DIGITS = "0123456789"
CBU_REGEX = r"^[0-9]{22}$"

def _create_cbu():
    flag = True
    while flag:
        random_cbu_suffix = ''.join(random.choice(DIGITS) for _ in range(CBU_SUFFIX_LEN))
        cbu = CBU_PREFIX + str(random_cbu_suffix)
        query = "SELECT COUNT(*) FROM accounts WHERE cbu = %(cbu)s"
        cursor.execute(query, {"cbu": cbu})
        result = cursor.fetchone()[0]
        if result == 0:
            flag = False
    return cbu

def _check_account_exists(cbu: str):
    query = "SELECT cbu, username, balance, afk_key FROM accounts WHERE cbu = %(cbu)s"
    cursor.execute(query, {"cbu": cbu})
    result = cursor.fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return result


#-----------------------------POST-----------------------------

# Endpoint para crear una cuenta
@app.post("/accounts")
def create_account(username: str):
    CBU = _create_cbu()
    query = "INSERT INTO accounts (cbu, username, balance) VALUES (%(cbu)s, %(username)s, %(balance)s)"
    values = {"cbu": CBU, "username": username, "balance": 0.0}
    cursor.execute(query, values)
    connection.commit()
    return {"cbu": CBU}

# Endpoint para modificar el saldo de una cuenta
@app.post("/accounts/{AFK_key}")
def modify_account_balance(amount: float, AFK_key: str):
    _check_account_exists(cbu)
    
    new_balance = float(result[2])
    new_balance += amount

    if new_balance < 0:
        raise HTTPException(status_code=403, detail="Insufficient funds")

    query = "UPDATE accounts SET balance = %(balance)s WHERE afk_key = %(AFK_key)s"
    values = {"balance": new_balance, "AFK_key": AFK_key}
    cursor.execute(query, values)
    connection.commit()
    return {"balance": new_balance}

#-----------------------------GET-----------------------------

# Endpoint para obtener todas las cuentas
@app.get("/accounts")
def get_all_accounts():
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
    
# Endpoint para obtener una cuenta específica
@app.get("/accounts/{cbu}")
def get_account(cbu: str = Path(..., regex=CBU_REGEX)):
    result = _check_account_exists(cbu)

    return {
        "cbu": result[0],
        "username": result[1],
        "balance": result[2],
        "afk_key": result[3]
    }

#-----------------------------PUT-----------------------------

# Endpoint para vincular una AFK key a una cuenta
@app.put("/accounts/{cbu}")
def link_afk_key_to_account(afk_key: str = None, cbu: str = Path(..., regex=CBU_REGEX)):
    _check_account_exists(cbu)

    query = "UPDATE accounts SET afk_key = %(afk_key)s WHERE cbu = %(cbu)s"
    values = {"afk_key": afk_key, "cbu": cbu}
    cursor.execute(query, values)
    connection.commit()
    return {"message": "Account successfully updated"}


#-----------------------------DELETE-----------------------------

# Endpoint para eliminar una cuenta
@app.delete("/accounts/{cbu}")
def delete_account(cbu: str = Path(..., regex=CBU_REGEX)):
    _check_account_exists(cbu)

    query = "DELETE FROM accounts WHERE cbu = %(cbu)s"
    cursor.execute(query, {"cbu": cbu})
    connection.commit()
    return {"message": "Account successfully deleted"}

@app.on_event("shutdown")
async def shutdown_event():
    cursor.close()
    connection.close()
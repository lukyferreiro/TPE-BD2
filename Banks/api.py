from fastapi import FastAPI, Path, HTTPException
from postgre_utils import *
import random

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
        NEW_CBU = CBU_PREFIX + random_cbu_suffix
        query = "SELECT COUNT(*) FROM accounts WHERE cbu = %(cbu)s"
        cursor.execute(query, {"cbu": NEW_CBU})
        result = cursor.fetchone()[0]
        if result == 0:
            flag = False
    return result


#-----------------------------POST-----------------------------

# Endpoint para crear una cuenta
@app.post("/accounts")
def create_account(username: str):
    CBU = _create_cbu()
    query = "INSERT INTO accounts (cbu, username, balance, afk_key) VALUES (%(cbu)s, %(username)s, %(balance)s, %(AFK_key)s)"
    values = {"cbu": CBU, "username": username, "balance": 0.0, "AFK_key": None}
    cursor.execute(query, values)
    connection.commit()
    return {"cbu": CBU}

# Endpoint para modificar el saldo de una cuenta
@app.post("/accounts/{AFK_key}")
def modify_account_balance(amount: float, AFK_key: str):
    query = "SELECT balance FROM accounts WHERE afk_key = %(afk_key)s"
    cursor.execute(query, {"afk_key": AFK_key})
    result = cursor.fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="Account not found")
    
    new_balance = result[0]
    new_balance += amount
    if new_balance < 0:
        raise HTTPException(status_code=403, detail="Insufficient funds")

    query = "UPDATE accounts SET balance = %(balance)s WHERE afk_key = %(AFK_key)s"
    values = (amount, {"balance": new_balance, "afk_key": AFK_key})
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
    query = "SELECT cbu, username, balance, afk_key FROM accounts WHERE cbu = %(cbu)s"
    cursor.execute(query, {"cbu": cbu})
    result = cursor.fetchone()
    
    if result is None:
        raise HTTPException(status_code=404, detail="Account not found")

    account = {
        "cbu": result[0],
        "username": result[1],
        "balance": result[2],
        "afk_key": result[3]
    }

    return account

#-----------------------------PUT-----------------------------

# Endpoint para vincular una AFK key a una cuenta
@app.put("/accounts/{cbu}")
def link_afk_key_to_account(afk_key: str, cbu: str = Path(..., regex=CBU_REGEX)):
    query = "SELECT COUNT(*) FROM accounts WHERE cbu = %(cbu)s"
    cursor.execute(query, {"cbu": cbu})
    result = cursor.fetchone()[0]
    if result == 0:
        raise HTTPException(status_code=404, detail="Account not found")

    query = "UPDATE accounts SET afk_key = %(afk_key)s WHERE cbu = %(cbu)s"

    # TODO habria que que ver una forma de que se pueda desvincular la afk_key de la cuenta
    # No se si esta muy bien esto
    if afk_key is None:
        update_values = {"afk_key": None, "cbu": cbu}
    else:
        update_values = {"afk_key": afk_key, "cbu": cbu}

    connection.commit()
    return {}

#-----------------------------DELETE-----------------------------

# Endpoint para eliminar una cuenta
@app.delete("/accounts/{cbu}")
def delete_account(cbu: str = Path(..., regex=CBU_REGEX)):
    query = "DELETE FROM accounts WHERE cbu = %(cbu)s"
    cursor = connection.cursor()
    cursor.execute(query, {"cbu": cbu})
    connection.commit()
    return {}
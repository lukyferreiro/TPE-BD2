from fastapi import HTTPException
from postgre_utils import cursor

def _check_account_exists_by_cbu(cbu: str):
    query = "SELECT cbu, username, balance, afk_key FROM accounts WHERE cbu = %(cbu)s"
    cursor.execute(query, {"cbu": cbu})
    result = cursor.fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return result

def _check_account_exists_by_key(afk_key: str):
    query = "SELECT cbu, username, balance, afk_key FROM accounts WHERE afk_key = %(afk_key)s"
    cursor.execute(query, {"afk_key": afk_key})
    result = cursor.fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return result
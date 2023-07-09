from fastapi import FastAPI, Path, Query, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from postgre_utils import connection, cursor
from mongo_utils import *
import hashlib
import requests
import psycopg2
from pydantic import EmailStr, constr, Field

def _check_user_exists(user_id: int):
    query = "SELECT userId, name, email, isBusiness FROM users WHERE userId = %(user_id)s"
    values = {"user_id": user_id}
    cursor = connection.cursor()
    cursor.execute(query, values)
    result = cursor.fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return result

def _check_user_exists_by_email(email: str):
    query = "SELECT userId, password, isBusiness FROM users WHERE email = %(email)s"
    values = {"email": email}
    cursor = connection.cursor()
    cursor.execute(query, values)
    result = cursor.fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return result

def _check_financial_entity_exists(financial_id: str):
    query = "SELECT financialId, name, apiLink FROM financialEntities WHERE financialId = %(financial_id)s"
    values = {"financial_id": financial_id}
    cursor = connection.cursor()
    cursor.execute(query, values)
    result = cursor.fetchone()
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return result

def _check_afk_key_exists(afk_key: str):
    query = "SELECT value, type, userId, financialId FROM afkKeys WHERE value = %(afk_key)s"
    values = {"afk_key": afk_key}
    cursor = connection.cursor()
    cursor.execute(query, values)
    result = cursor.fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="Key not found")
    return result

def _check_relation_user_key(user_id: int, afk_key: str):
    query = "SELECT COUNT(*) FROM afkKeys WHERE userId = %(user_id)s AND value = %(afk_key)s"
    values = {"user_id": user_id, "afk_key": afk_key}
    cursor = connection.cursor()
    cursor.execute(query, values)
    results = cursor.fetchall()
    if len(results) == 0:
        raise HTTPException(status_code=400, detail="Invalid operation")

def _get_api_link_from_afk_key(afk_key: str, who: str):
    query = """ 
        SELECT financialEntities.apiLink FROM afkKeys JOIN financialEntities 
        ON afkKeys.finacialId = financialEntities.finacialId WHERE afkKeys.value = %(afk_key)s
    """
    values = {"afk_key": afk_key}
    cursor = connection.cursor()
    cursor.execute(query, values)
    result = cursor.fetchone()

    if result is None:
        raise HTTPException(status_code=404, detail=f"AFK key {who} not found")

    return result[0]

def _validate_credentials(email: str, password: str):
    result_user = _check_user_exists_by_email(email)

    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    if result_user[1] == hashed_password:
        return result_user[0], result_user[2]

    raise HTTPException(status_code=401, detail="Invalid credentials")

def _delete_user_from_id(user_id: int):
    query = "DELETE FROM users WHERE userId = %(user_id)s"
    values = {"user_id": user_id}
    cursor.execute(query, values)
    connection.commit()

def _delete_afk_key(afk_key: int):
    query = "DELETE FROM afkKeys WHERE value = %(afk_key)s"
    values = {"afk_key": afk_key}
    cursor.execute(query, values)
    connection.commit()
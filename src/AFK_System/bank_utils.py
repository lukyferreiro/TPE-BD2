from fastapi import HTTPException
from api_utils import _delete_afk_key
import requests
from mongo_utils import collection
from pymongo.errors import PyMongoError
import pytz
from datetime import datetime

def _unlink_key_from_account(apiLink: str, afk_key: str):
    url = f"{apiLink}/accounts/account/unlink"
    body = {'afk_key': afk_key}
    
    try:
        response = requests.put(url=url, json=body)
        response.raise_for_status() 
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])

    return response

def _link_key_from_account(apiLink: str, afk_key: str, cbu: str):
    url = f"{apiLink}/accounts/account/link"
    body = {
        'afk_key': f"{afk_key}",
        'cbu': f"{cbu}"
    }

    try:
        response = requests.put(url, json=body)
        response.raise_for_status() 
    except requests.exceptions.RequestException as e:
        # Rollbackeamos si falla el pedido al banco
        _delete_afk_key(afk_key)
        raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])
    
    return response

def _get_balance_from_account(apiLink: str, afk_key: str):
    url = f"{apiLink}/accounts/account/balance"
    params = {'afk_key': afk_key}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status() 
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])

    return response    

def _make_transaction(apiLink_from: str, apiLink_to: str, amount: float, afk_key_from: str, afk_key_to: str, user_id_from: int):
    url_from = f"{apiLink_from}/accounts/account"
    body_from = {
        'afk_key': f"{afk_key_from}",
        'amount': -amount
    }
    response_from = requests.post(url_from, json=body_from)

    if response_from.status_code == 200:
        url_from = f"{apiLink_to}/accounts/account"
        body_to = {
            'afk_key': f"{afk_key_to}",
            'amount': amount
        }
        response_to = requests.post(url_from, json=body_to)

        if response_to.status_code == 200:
            # Si funcionaron ambas transacciones, guardamos la transaccion en MongoDB
            argentina_tz = pytz.timezone('America/Argentina/Buenos_Aires')
            current_datetime = datetime.now()
            current_datetime = current_datetime.astimezone(argentina_tz)
            formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

            transaction_data = {
                "to": afk_key_to,
                "from": afk_key_from,
                "amount": amount,
                "date": formatted_datetime,
                "userId_from": user_id_from
            }       
            try:
                result = collection.insert_one(transaction_data)
                print("Transacción insertada con éxito. ObjectID:", result.inserted_id)
            except PyMongoError as e:
                print("Error al insertar documento:", e)

        else: 
            # Si falla la segunda transacción, le devuelvo al primer usuario su dinero
            url_from = f"{apiLink_from}/accounts/account"
            body_from = {
                'afk_key': f"{afk_key_from}",
                'amount': amount
            }
            response_from = requests.post(url_from, json=body_from)
            raise HTTPException(status_code=response_to.status_code, detail=response_to.json()['detail'])
            
    else :
        raise HTTPException(status_code=response_from.status_code, detail=response_from.json()['detail'])
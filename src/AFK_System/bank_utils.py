from fastapi import HTTPException
from api_utils import _delete_afk_key
import requests

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
        'afk_key': f"{value}",
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
    url = f"{result_finacial_entity[2]}/accounts/account/balance"
    params = {'afk_key': afk_key}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status() 
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail="Error al procesar la solicitud")

    return response    
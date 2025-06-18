
import base64
import logging
from typing import Any, List, Optional

import requests
from multiversx_sdk_core.serializer import args_to_strings


def sync_sc_query(sc_address: str,
                  function: str,
                  args: List[Any] = []) -> Optional[List[str]]:
    query = _prepare_query(sc_address, function, args)

    url = f'https://gateway.multiversx.com/vm-values/query'

    try:
        json_ = requests.post(url,
                              json=query).json()

        return _decode_json(json_)
    except Exception as e:
        logging.exception('Error during sync query')
        logging.error(
            f'Error during query - parameters :: {sc_address} :: {function} :: {args}')
        return None


def _decode_json(json_) -> Optional[List[str]]:
    try:
        code = json_['code']

        if code == 'successful':
            rdata = json_['data']['data']['returnData']
            if rdata is None:
                res = None
            else:
                res = [base64.b64decode(x).hex() for x in rdata]
        else:
            res = None
    except:
        logging.error('Error during query')
        res = None

    return res


def _prepare_query(sc_address: str,
                   function: str,
                   args: List[Any]):

    prepared_args = args_to_strings(args)

    return {
        "scAddress": sc_address,
        "funcName": function,
        "value": "0",
        "args": prepared_args
    }

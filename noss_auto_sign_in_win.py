import hashlib
import json
import random
import string
import threading
import time

import bech32
import ecdsa
import requests
import websocket
from loguru import logger
from pynostr.key import PrivateKey
from web3 import Web3

# Arbitrum prc node url
arbitrum_rpc_url = "https://rpc.arb1.arbitrum.gateway.fm"

web3 = Web3(Web3.HTTPProvider(arbitrum_rpc_url))

last_event_id = ''


def get_last_event_id_forever():
    websocket_url = 'ws://report-worker-2.noscription.org/'

    ws = websocket.WebSocketApp(websocket_url,
                                header={
                                    'Pragma': 'no-cache',
                                    'Origin': 'https://noscription.org',
                                    'Accept-Language': 'zh-CN,zh;q=0.9',
                                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                                    'Upgrade': 'websocket',
                                    'Cache-Control': 'no-cache',
                                    'Connection': 'Upgrade',
                                    'Sec-WebSocket-Version': '13',
                                })

    def on_message(ws, message):
        global last_event_id
        try:
            eventId = json.loads(message)["eventId"]
            if last_event_id != eventId:
                last_event_id = eventId
                logger.debug(f"update last_event_id: {last_event_id}...")

        except:
            logger.error("get last_event_id json parse error|message: {message}")

    ws.on_message = on_message
    # websocket.enableTrace(True)
    # ws = websocket.WebSocketApp(websocket_url, header={'Sec-WebSocket-Extensions': ''})

    ws.run_forever(reconnect=True)


def get_latest_arb_block():
    while True:
        if web3.is_connected():
            latest_block_number = web3.eth.block_number
            latest_block_hash = web3.eth.get_block(latest_block_number)['hash'].hex()
            logger.info(f"The latest block number is: {latest_block_number}, {latest_block_hash}")
            return str(latest_block_number), latest_block_hash
        else:
            logger.error("cannot connect to Arbitrum network, retrying...")


def get_nonce():
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))[2:15]
    return random_string


def get_hash_sign(json_str: str):
    # dict to str

    hash_object = hashlib.sha256()
    hash_object.update(json_str.encode('utf-8'))
    result = hash_object.hexdigest()
    return result


# no use age
def get_event_id(data: list):
    json_str = json.dumps(data, indent=None, separators=(',', ':'))
    r = get_hash_sign(json_str)
    return r


def get_id(data):
    json_str = json.dumps(data, indent=None, separators=(',', ':'))
    r = get_hash_sign(json_str)
    return r


def decode_bech32(encoded_key):
    _, data = bech32.bech32_decode(encoded_key)
    if data is None:
        raise ValueError("Invalid Bech32 key")
    return bytes(bech32.convertbits(data, 5, 8, False))


def sign_msg(message, private_key):
    decoded_private_key = decode_bech32(private_key)

    private_key = ecdsa.SigningKey.from_string(decoded_private_key, curve=ecdsa.SECP256k1)

    message_str = message["id"]

    signature = private_key.sign(message_str.encode('utf-8'), hashfunc=hashlib.sha256)

    # print("Signature:", signature.hex())
    return signature.hex()


def post_event(payload: dict):
    headers = {
        "authority": "api-worker.noscription.org",
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9",
        "content-type": "application/json",
        "origin": "https://noscription.org",
        "referer": "https://noscription.org/",
        "sec-ch-ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    url = "https://api-worker.noscription.org/inscribe/postEvent"
    data = json.dumps(payload, separators=(',', ':'))
    # print(data)
    response = requests.post(url, headers=headers, data=data)

    logger.info(f"post event response: {response.text}")


def main(pubkey, private_key):
    cache_event_id = 'xxx'
    start_time = time.time()
    while True:
        if not last_event_id:
            logger.warning("last_event_id is empty, retrying...")
            time.sleep(0.1)
        if last_event_id != cache_event_id:
            cache_event_id = last_event_id
            logger.warning("event_id updated, to update block_height and block_hash...")
            block_height, block_hash = get_latest_arb_block()
            create_at_timestamp = int(time.time())
        nonce = get_nonce()

        data = [
            0,
            pubkey,
            # create at
            # 1704195456,
            create_at_timestamp,
            # kind
            1,
            # tags
            [
                [
                    "p",
                    "9be107b0d7218c67b4954ee3e6bd9e4dba06ef937a93f684e42f730a0c3d053c"
                ],
                [
                    "e",
                    "51ed7939a984edee863bfbb2e66fdc80436b000a8ddca442d83e6a2bf1636a95",
                    "wss://relay.noscription.org/",
                    "root"
                ],
                [
                    "e",
                    last_event_id,
                    "wss://relay.noscription.org/",
                    "reply"
                ],
                [
                    "seq_witness",
                    block_height,
                    block_hash
                ],
                [
                    "nonce",
                    nonce,
                    "21"
                ]
            ],
            "{\"p\":\"nrc-20\",\"op\":\"mint\",\"tick\":\"noss\",\"amt\":\"10\"}"
        ]

        _id = get_id(data)
        # print("nonce: ", nonce, "id: ", _id)
        if _id.startswith("00000"):
            break
    message = {
        "id": _id,
        "kind": 1,
        "created_at": create_at_timestamp,
        "tags": [
            [
                "p",
                "9be107b0d7218c67b4954ee3e6bd9e4dba06ef937a93f684e42f730a0c3d053c"
            ],
            [
                "e",
                "51ed7939a984edee863bfbb2e66fdc80436b000a8ddca442d83e6a2bf1636a95",
                "wss://relay.noscription.org/",
                "root"
            ],
            [
                "e",
                last_event_id,
                "wss://relay.noscription.org/",
                "reply"
            ],
            [
                "seq_witness",
                block_height,
                block_hash
            ],
            [
                "nonce",
                nonce,
                "21"
            ]
        ],
        "content": "{\"p\":\"nrc-20\",\"op\":\"mint\",\"tick\":\"noss\",\"amt\":\"10\"}",
        "pubkey": pubkey
    }

    sig = sign_msg(message, private_key)

    #  post event
    pay_load = {
        "event": {
            "sig": sig,
            "id": _id,
            "kind": 1,
            "created_at": create_at_timestamp,
            "tags": [
                [
                    "p",
                    "9be107b0d7218c67b4954ee3e6bd9e4dba06ef937a93f684e42f730a0c3d053c"
                ],
                [
                    "e",
                    "51ed7939a984edee863bfbb2e66fdc80436b000a8ddca442d83e6a2bf1636a95",
                    "wss://relay.noscription.org/",
                    "root"
                ],
                [
                    "e",
                    last_event_id,
                    "wss://relay.noscription.org/",
                    "reply"
                ],
                [
                    "seq_witness",
                    block_height,
                    block_hash
                ],
                [
                    "nonce",
                    nonce,
                    "21"
                ]
            ],
            "content": "{\"p\":\"nrc-20\",\"op\":\"mint\",\"tick\":\"noss\",\"amt\":\"10\"}",
            "pubkey": pubkey
        }
    }

    logger.success(
        f"successful! cost: {round(time.time() - start_time, 2)}s, nonce: {nonce}, id: {_id}, sig: {sig}, event: {cache_event_id}")
    post_event(pay_load)
    logger.success(f" post id event successfuf : {_id}")
    print(_id)


def rush(pubkey, private_key):
    while True:
        main(pubkey, private_key)


if __name__ == '__main__':

    # type_your_private_key_here
    private_key = "xxxxxxxxx"

    identity_pk = PrivateKey.from_nsec(private_key)

    pubkey = identity_pk.public_key.hex()

    thread_num = 10

    # update last_event_id forever in background
    for i in range(1):
        i = threading.Thread(target=get_last_event_id_forever, args=())
        i.start()

    time.sleep(3)
    # thread num -> 10
    for i in range(thread_num):
        i = threading.Thread(target=rush, args=(pubkey, private_key))
        i.start()

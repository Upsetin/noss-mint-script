import json

from nostr_sdk import Keys


def generate_keys(key_number: int):
    key_list = []
    for i in range(key_number):
        keys = Keys.generate()
        key_dict = {
            "private_key": keys.secret_key().to_bech32(),
            "public_key": keys.public_key().to_bech32(),
            "account_id": i,
        }
        key_list.append(key_dict)

    f = open("keys.json", "w")
    json.dump(key_list, f, indent=4)


if __name__ == '__main__':
    key_number = 100
    generate_keys(key_number)

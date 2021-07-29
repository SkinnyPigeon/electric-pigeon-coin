from hashlib import sha256
import json


def hash_string_256(string):
    return sha256(string).hexdigest()

def hash_block(block):
    return hash_string_256(json.dumps(block, sort_keys=True).encode())

import datetime
import json
from typing import Any, Tuple
import hashlib


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if o is None:
            super().default(o)
        elif isinstance(o, datetime.datetime):
            return o.isoformat()
        elif CustomJSONEncoder.has_jsonify_method(o):
            return o.__jsonify__()
        else:
            super().default(o)

    @staticmethod
    def has_jsonify_method(obj) -> bool:
        return hasattr(obj, "__jsonify__") and callable(getattr(obj, "__jsonify__"))


def hash_file(path: str):
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


def find_match(lst: list, predicate):
    for i, v in enumerate(lst):
        if predicate(v):
            return i, v
    return None, None

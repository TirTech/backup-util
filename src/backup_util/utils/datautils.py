import datetime
import hashlib
import json
import os
from typing import Any, Tuple, Optional


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


def find_match(lst: list, predicate) -> Tuple[Optional[int], Optional[Any]]:
    for i, v in enumerate(lst):
        if predicate(v):
            return i, v
    return None, None


def path_common_suffix(p1: str, p2: str) -> str:
    head1, tail1 = os.path.split(p1)
    head2, tail2 = os.path.split(p2)
    res = ""
    while tail1 == tail2 and len(head1) > 0 and len(head2) > 0:
        if res == "":
            res = tail1
        else:
            res = os.path.join(tail1, res)
        head1, tail1 = os.path.split(head1)
        head2, tail2 = os.path.split(head2)
    return res

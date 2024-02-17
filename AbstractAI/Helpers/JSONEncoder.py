import json
from enum import Enum
from datetime import datetime
from torch import dtype

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return f"<{type(obj).__name__}>.{obj.value}"
        if isinstance(obj, datetime):
            if obj.tzinfo is not None and obj.tzinfo.utcoffset(obj) is not None:
                return obj.strftime("%Y-%m-%d %H:%M:%S.%f %z")
            else:
                return obj.strftime("%Y-%m-%d %H:%M:%S.%f")
        if isinstance(obj, dtype):
            return f"<dtype>(is_floating_point:is_floating_point={obj.is_floating_point}, is_complex={obj.is_complex}, is_signed={obj.is_signed}, itemsize={obj.itemsize})"
        return json.JSONEncoder.default(self, obj)
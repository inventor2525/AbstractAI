import json
from enum import Enum
from datetime import datetime

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return f"<{type(obj).__name__}>.{obj.value}"
        if isinstance(obj, datetime):
            if obj.tzinfo is not None and obj.tzinfo.utcoffset(obj) is not None:
                return obj.strftime("%Y-%m-%d %H:%M:%S.%f %z")
            else:
                return obj.strftime("%Y-%m-%d %H:%M:%S.%f")
        return json.JSONEncoder.default(self, obj)
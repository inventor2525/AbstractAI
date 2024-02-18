from torch import dtype

from ClassyFlaskDB.serialization import JSONEncoder
JSONEncoder.add_formatting_rule(
	lambda obj: isinstance(obj, dtype),
	lambda obj: f"<dtype>(is_floating_point:is_floating_point={obj.is_floating_point}, is_complex={obj.is_complex}, is_signed={obj.is_signed}, itemsize={obj.itemsize})"
)
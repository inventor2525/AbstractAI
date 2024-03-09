from ClassyFlaskDB.serialization import JSONEncoder

def fast_is_dtype(obj):
	'''
		Checks if the object is a torch.dtype object without having to import torch.
	'''
	return str(type(obj)) == "<class 'torch.dtype'>" and hasattr(obj, "is_floating_point") and hasattr(obj, "is_complex") and hasattr(obj, "is_signed") and hasattr(obj, "itemsize")

JSONEncoder.add_formatting_rule(
	lambda obj: fast_is_dtype(obj),
	lambda obj: f"<dtype>(is_floating_point:is_floating_point={obj.is_floating_point}, is_complex={obj.is_complex}, is_signed={obj.is_signed}, itemsize={obj.itemsize})"
)
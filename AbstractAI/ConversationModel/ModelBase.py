from ClassyFlaskDB.DATA import DATADecorator, field
from datetime import datetime
import tzlocal

def get_local_time():
	local_tz = tzlocal.get_localzone()
	return datetime.now(local_tz)

# Define a decorator instance that we can use to create our whole 
# conversation model, and latter attach it to any SQL instance.
DATA = DATADecorator()
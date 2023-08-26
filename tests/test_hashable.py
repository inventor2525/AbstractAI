import unittest
from AbstractAI.Conversation import *

class TestHashable(unittest.TestCase):
	def test_edit_source_hash(self):
		es = EditSource(None, None)
		initial_hash = es.hash

		es.original = Message("content", Role.Assistant)
		ct = es.original.creation_time
		self.assertNotEqual(initial_hash, es.hash)
		initial_hash = es.hash
		
		es.original = Message("content", Role.Assistant)
		self.assertNotEqual(initial_hash, es.hash)

		es.original = Message("content", Role.Assistant)
		es.original.creation_time = ct
		self.assertEqual(initial_hash, es.hash)

if __name__ == '__main__':
	unittest.main()
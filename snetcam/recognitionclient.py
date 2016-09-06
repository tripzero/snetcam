#recognitionclient.py

import trollius as asyncio
import json

from wss import Client

from recognitionserver import Messages

class C:

	class_map = {}

	@staticmethod
	def message_handler(id):
		def make_message_handler(_cls):

			if id in C.class_map:
				raise Exception("{} message handler is already implemented".format(id))
			C.class_map[id]=_cls
			return _cls
		return make_message_handler

	@staticmethod
	def new(id, data_obj):
		return C.class_map[id](data_obj)

def cls(c):
	print("class = {}".format(type(c).__name__))
	return type(c).__name__



class RecognitionClient:
		
	def __init__(self, camera_name, address="localhost", port=9004, usessl=False):

		self.msgRecieved = {}
		self.camera_name = camera_name
		
		self.client = Client(retry=True)
		self.client.connectTo(address, port, useSsl=usessl)
		
		self.client.setTextHandler(self.txtHndler)
		self.client.setOpenHandler(self.connection_opened)

		self.openHandler = None

	def connection_opened(self):
		try:
			self.select_camera(self.camera_name)
			if self.openHandler:
				self.openHandler()

		except:
			import sys, traceback
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			traceback.print_exception(exc_type, exc_value, exc_traceback,
					limit=6, file=sys.stdout)

	def setOpenHandler(self, callback):
		self.openHandler = callback

	def select_camera(self, camera_name):	
		self.client.sendTextMsg(Messages.select_camera(camera_name))

	def list_users(self):
		self.client.sendTextMsg(Messages.list_users())
		
	def txtHndler(self, data):

		data_obj = json.loads(data)

		if "signal" in data_obj:
			self.hndlSignal(data_obj)

	def hndlSignal(self, data_obj):
		msg_class = data_obj["signal"]
		
		if msg_class in C.class_map:
			print ("trace")
			c = C.class_map[msg_class]
			msg = c(data_obj)
			
			if c in self.msgRecieved:
				self.msgRecieved[c](msg)

	def setMessageReceived(self, msg_type, callback):
		self.msgRecieved[msg_type] = callback


class MessageBase(object):

	def __init__(self, data_obj):
		for key in data_obj.keys():
			if hasattr(self, key):
				setattr(self, key, data_obj[key])

@C.message_handler("face_detected")
class FaceDetectedSignal(MessageBase):
	"""
	face_detected

	args: 
	img - img data.  byte64 encoded jpeg

	example:
	{"signal" : "face_detected", "img" : "..."}
	"""
	
	def __init__(self, data_obj):
		self.image = None

		MessageBase.__init__(self, data_obj)

@C.message_handler("face_recognized")
class FaceRecognizedSignal(MessageBase):
	"""
	protocl: 

	signal:
	face_recognized

	example:
	{
		"signal" : "face_recognized",
		"username" : "unknown",
		"uuid" : "1235ABCD..."
		"realname" : "Unknown User",
		"img" : "..."
	}

	"""
	def __init__(self, data_obj):
		self.username = None
		self.uuid = None
		self.realname = None
		self.img = None

		MessageBase.__init__(self, data_obj)

@C.message_handler("list_users")
class ListUsersSignal(MessageBase):
	"""
	list_users

	example:
	{ "signal" : "list_users", "users" : [...]}
	"""

	def __init__(self, data_obj):
		self.users = []

		MessageBase.__init__(self, data_obj)

if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('address', help="address", default="localhost", nargs="?")
	parser.add_argument('port', help="port", default=9004, nargs="?")
	parser.add_argument('--ssl', dest="usessl", help="use ssl.", action='store_true')
	parser.add_argument('--camera_name', help="name of camera")
	args = parser.parse_args()

	client = RecognitionClient(args.camera_name, args.address, args.port, args.usessl)
	
	def connected():
		client.list_users()

	client.setOpenHandler(connected)

	def face_recognized(msg):
		print("face_recognized received: {}".format(msg.username))

	def face_detected(msg):
		print("face_recognized received: {}")

	def list_users(msg):
		for user in msg.users:
			print("user: {}".format(user["username"]))

	client.setMessageReceived(FaceRecognizedSignal, face_recognized)
	client.setMessageReceived(FaceDetectedSignal, face_detected)
	client.setMessageReceived(ListUsersSignal, list_users)

	asyncio.get_event_loop().run_forever()

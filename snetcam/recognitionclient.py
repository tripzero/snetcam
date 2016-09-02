#recognitionclient.py

from wss import Client
import json

class C:

	class_map = {}

	@staticmethod
	def message_handler(id):
		def make_message_handler(cls):

			if id in C.class_map:
				raise Exception("{} message handler is already implemented".format(id))
			C.class_map[id]=cls
			return cls
		return make_message_handler

	@staticmethod
	def new(id, data_obj):
		return C.class_map[id](data_obj)


class RecognitionClient:
		
	def __init__(self, camera_name, address="localhost", port=9004):
		self.client = Client(retry=True)
		self.client.connectTo(address, port)

		self.client.sendTextMsg('{ "method" : "select_camera", "camera" : "{}" }'.format(camera_name))
		
		self.setTextHandler(self.txtHndler)
		
	def txtHndler(self, data):

		data_obj = json.loads(data)

		if "signal" in data_obj:
			self.hndlSignal(data_obj)

	def hndlSignal(self, data_obj):
		msg_class = data_obj["signal"]

		if msg_class in C.class_map:
			msg = C.class_map[msg_class](data_obj)


class MessageBase(object):

	def __init__(self, data_obj):
		for key in data_obj.keys:
			if hasattr(self, key):
				setattr(self, key, data_obj[key])

@C.message_handler("face_detected")
class FaceDetectedSignal(MessageBase):
	"""
	face_detected

	args: 
	data - img data.  byte64 encoded jpeg

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


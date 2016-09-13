from wss import Server
from .FaceRecognition import FaceRecognition
import json
import trollius as asyncio
from base64 import b64decode, b64encode
import numpy as np
import cv2

from .recognitionprotocol import Messages, Signals, ErrorMessages


class CameraBase:

	def __init__(self, name, maxsize=0):
		self.imgQueue = asyncio.Queue(maxsize)
		self.name = name


class RecognitionServer(Server):

	def __init__(self, cameras=[], port=9004, dbfile="faces.db"):
		
		Server.__init__(self, port=port, usessl=False)

		self.camera_clients = {}
		self.recognizer = FaceRecognition(db=dbfile)
		users, faces = self.recognizer.trainFromDatabase()

		print("we have {} users and {} faces".format(users, faces))

		self.cameras = cameras
		self.start()

		self.method_handlers = {}
		self.method_handlers["list_users"] = self.list_users
		self.method_handlers["select_camera"] = self.select_camera

		asyncio.get_event_loop().create_task(self.poll())

	
	def send_all(self, camera_name, msg):
		for client in self.camera_clients[camera_name]:
			client.sendMessage(msg, False)

	def face_detected(self, img, camera_name):		
		if not camera_name in self.camera_clients:
			return

		msg = Signals.face_detected(img)
		
		self.send_all(camera_name, msg)

	def face_recognized(self, img, user, camera_name):
		if not camera_name in self.camera_clients:
			return
		
		msg = Signals.face_recognized(user, img)

		self.send_all(camera_name, msg)


	@asyncio.coroutine
	def poll(self):
		while True:
			
			for camera in self.cameras:
				try:
					img = yield asyncio.From(camera.imgQueue.get())
					self.process(img, camera.name)
				except KeyboardInterrupt:
					raise KeyboardInterrupt()
				except:
					print("we b0rked trying to get img from {}".format(camera.name))


	def process(self, img, camera_name):
		
		faces = self.recognizer.detectFaces(img)

		if not len(self.recognizer.users) and len(faces):
			return

		for face in faces:
			try:
				self.face_detected(face, camera_name)
				user = self.recognizer.recognize(face)

				if not user:
					return

				confidence = user["confidence"]
				uuid = user["uuid"]

				print("user recognized: {}".format(user))
				print("confidence: {}".format(confidence))

				if confidence < 700:
					self.recognizer.addFaceToUser(uuid, face, confidence)
					
				elif confidence > 800:
					self.face_recognized(face, user, camera_name)

			except:
				import sys, traceback
				exc_type, exc_value, exc_traceback = sys.exc_info()
				traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
				traceback.print_exception(exc_type, exc_value, exc_traceback,
							limit=6, file=sys.stdout)

	def onMessage(self, msg, fromClient):
		print("message received!!!")

		msg = json.loads(msg)

		if "method" in msg.keys():
			self.hndl_method(msg, fromClient)

	def hndl_method(self, msg, fromClient):
		method = msg["method"]
		if method in self.method_handlers:
			self.method_handlers[method](msg, fromClient)

	def select_camera(self, msg, fromClient):
		if not "camera" in msg:
			print("Error: invalid select_camera message")
			return

		camera_name = msg["camera"]

		valid_camera = False

		for camera in self.cameras:
			if camera.name == camera_name:
				valid_camera = True
				break

		if not valid_camera:
			fromClient.sendMessage(Signals.error(ErrorMessages.InvalidCamera), False)
			return

		if not camera_name in self.camera_clients.keys():
			self.camera_clients[camera_name] = []

		self.camera_clients[camera_name].append(fromClient)

	def list_users(self, msg, fromClient):
		filter=None
		if "filter" in msg:
			filter = msg["filter"]

		reply = Signals.list_users(self.recognizer.getUsers(filter))

		fromClient.sendMessage(reply, False)
		


class LocalCamera(CameraBase):

	def __init__(self, name, cam_dev=0):
		CameraBase.__init__(self, name, maxsize=5)

		asyncio.get_event_loop().create_task(self.poll_camera(cam_dev))

	@asyncio.coroutine
	def poll_camera(self, cam_dev):
		import cv2
		cap = cv2.VideoCapture(cam_dev)

		while True:
			try:
				ret, img = cap.read()
				if not ret:
					print("error reading from camera")
					return

				self.imgQueue.put_nowait(img)

			except asyncio.QueueFull:
				pass
			except KeyboardInterrupt:
				raise KeyboardInterrupt()

			except:
				print("error polling camera")

			yield asyncio.From(asyncio.sleep(1/30))

class WssCamera(CameraBase):
	def __init__(self, name, address, port, use_ssl=False):
		CameraBase.__init__(self, name, maxsize=5)

		self.address = address
		self.port = port

		from wss import Client

		client = Client(retry=True)
		client.setTextHandler(self.img_received)
		client.connectTo(self.address, self.port, useSsl=use_ssl)

	def img_received(self, payload):
		payload = b64decode(payload)
		img = np.frombuffer(payload, dtype='uint8')
		img = cv2.imdecode(img, cv2.IMREAD_COLOR)

		try:
			self.imgQueue.put_nowait(img)
		except asyncio.QueueFull:
			pass
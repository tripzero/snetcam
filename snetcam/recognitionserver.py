from wss import Server
from FaceRecognition import FaceRecognition
import json
import trollius as asyncio


class CameraBase:

	def __init__(self, name, maxsize=0):
		self.imgQueue = asyncio.Queue(maxsize)
		self.name = name

class RecognitionServer:

	def __init__(self, cameras=[], port=9004, dbfile="faces.db"):
		self.camera_clients = {}
		self.recognizer = FaceRecognition(db=dbfile)
		users, faces = self.recognizer.trainFromDatabase()

		print("we have {} users and {} faces".format(users, faces))

		self.cameras = cameras
		self.server = Server(port=port)

		self.method_handlers = {}
		self.method_handlers["list_users"] = self.list_users
		self.method_handlers["select_camera"] = self.select_camera

		asyncio.get_event_loop().create_task(self.poll())

	@asyncio.coroutine
	def poll(self):
		while True:
			
			for camera in self.cameras:
				try:
					img = yield asyncio.From(camera.imgQueue.get())
					self.process(img)
				except:
					print("we b0rked trying to get img from {}".format(camera.name))


	def process(self, img):
		
		faces = self.recognizer.detectFaces(img)
		print("number of faces in image: {}".format(len(faces)))
		print("number of users: {}".format(len(self.recognizer.users)))

		if not len(self.recognizer.users) and len(faces):
			new_user = self.recognizer.createUser("the_unknown_face", faces)
			return

		for face in faces:
			try:
				user = self.recognizer.recognize(face)
				print("user recognized: {}".format(user))

				if user["confidence"] <= 10:
					"The could be a new user.  Create unknown user for this face for future identification."
					self.recognizer.createUser("the_unknown_face", [face])

			except:
				import sys, traceback
				exc_type, exc_value, exc_traceback = sys.exc_info()
				traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
				traceback.print_exception(exc_type, exc_value, exc_traceback,
							limit=6, file=sys.stdout)

	def onMessage(self, msg, fromClient):

		msg = json.loads(msg)

		if "method" in msg.keys():
			self.hndl_method(msg, fromClient)

	def hndl_method(self, msg):
		method = msg["method"]
		if method in self.method_handlers:
			self.method_handlers[method](msg)

	def select_camera(self, msg):
			camera_name = msg["camera"]

			if not camera_name in self.camera_clients.keys():
				self.camera_clients[camera_name] = []

			self.camera_clients[camera_name].append(fromClient)


	def list_users(self, msg):
			filter=None
			if "filter" in msg:
				filter = msg["filter"]

			reply = {"signal" : "list_users"}
			reply["users"] = self.recognizer.getUsers(filter)

			fromClient.sendMessage(json.dumps(reply), False)
		


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
		client.connectTo(self.address, self.port, useSsl=args.use_ssl)

if __name__ == "__main__":

	cam = LocalCamera("test_cam")
	serv = RecognitionServer([cam])

	asyncio.get_event_loop().run_forever()
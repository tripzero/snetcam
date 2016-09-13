class Messages:

	@staticmethod
	def list_users(filter = None):
		msg = { "method" : "list_users", "filter": filter}
		return json.dumps(msg)

	@staticmethod
	def select_camera(camera_name):
		msg = { "method" : "select_camera", "camera" : camera_name }
		return json.dumps(msg)

class Signals:
	
	@staticmethod
	def encode_img(img):
		success, data = cv2.imencode('.jpg', img)

		if not success:
			print("failed to encode image")
			return None

		data = np.getbuffer(data)
		data = bytes(data)
		data = b64encode(data)
		return data

	@staticmethod
	def face_detected(img):
		data = Signals.encode_img(img)
		msg = {"signal": "face_detected", "img": data}
		return json.dumps(msg)

	@staticmethod
	def face_recognized(user, img):
		data = Signals.encode_img(img)
		msg = {"signal": "face_recognized", "username": user["username"],
		       "uuid": user["uuid"],
		       "realname": user["realname"],
		       "img": data}
		return json.dumps(msg)

	@staticmethod
	def list_users(users):
		msg = {"signal" : "list_users", "users" : users }
		return json.dumps(msg)

	@staticmethod
	def error(msg):
		msg = {"signal" : "error", "message" : msg}
		return json.dumps(msg)

class ErrorMessages:

	InvalidCamera = "Invalid camera selected"
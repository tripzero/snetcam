import json
from base64 import b64decode, b64encode
import numpy as np

class Messages:

	@staticmethod
	def list_users(filter = None):
		msg = { "method" : "list_users", "filter": filter}
		return json.dumps(msg)

	@staticmethod
	def list_users_with_level(level):
		msg = { "method" : "list_users_with_level", "level": level}
		return json.dumps(msg)

	@staticmethod
	def select_camera(camera_name):
		msg = { "method" : "select_camera", "camera" : camera_name }
		return json.dumps(msg)

	@staticmethod
	def add_association(uuid, associate_uuid):
		msg = { "method" : "add_association", "uuid" : uuid, "associate_uuid" : associate_uuid }
		return json.dumps(msg)

	@staticmethod
	def retrain():
		msg = { "method" : "retrain" }
		return json.dumps(msg)

class Signals:
	
	@staticmethod
	def encode_img(img):

		import cv2
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
		#data = Signals.encode_img(img)
		data = None
		msg = {"signal": "face_detected", "img": data}
		return json.dumps(msg)

	@staticmethod
	def persons_detected(persons, users):
		tracking_ids = []

		for p in persons:
			tracking_ids.append(p.tracking_id)

		users_n = []

		for u in users:
			users_n.append(u.to_json())

		msg = { "signal" : persons_detected,
			"num_persons" : len(persons), 
			"tracking_ids": tracking_ids,
			"num_users" : len(users_n),
			"users" : users_n
		}

		return json.dumps(msg)

	@staticmethod
	def face_recognized(user, img, confidence):
		#data = Signals.encode_img(img)
		data = None
		msg = user.to_json()
		msg["signal"] = "face_recognized"
		msg["img"] = data
		msg["confidence"] = confidence
		
		return json.dumps(msg)

	@staticmethod
	def list_users(users):
		msg = {"signal" : "list_users", "users" : users }
		return json.dumps(msg)

	@staticmethod
	def list_users_with_level(users):
		msg = {"signal" : "list_users_with_level", "users" : users }
		return json.dumps(msg)

	@staticmethod
	def error(msg):
		msg = {"signal" : "error", "message" : msg}
		return json.dumps(msg)

class ErrorMessages:

	InvalidCamera = "Invalid camera selected"
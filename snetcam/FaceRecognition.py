#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import sqlite3
import base64
import json
import datetime
import time

from .FaceDatabase import FaceDatabase

logfile = open("FaceRecognition.log", "w")

def debug(msg):
	logfile.write("{0}\n".format(msg))
	logfile.flush()

debug("Starting log: {0}".format(datetime.datetime.now()))

class FaceRecognition():
	def __init__(self, useOpenCL = False, db = "myfaces.db"):
		self.trainingSize = (100, 75)
		debug("instantiating FaceRecognition")
		self.db = db
		self.users = []

		#self.faceCascade = cv2.CascadeClassifier("/usr/share/OpenCV/lbpcascades/lbpcascade_frontalface.xml")
		self.faceCascade = cv2.CascadeClassifier("/usr/share/OpenCV/haarcascades/haarcascade_frontalface_default.xml")
		self.recognizer = cv2.face.createEigenFaceRecognizer();
		cv2.ocl.setUseOpenCL(useOpenCL)

		#self.trainFromDatabase()

	def detectFaces(self, frame):
		grayImg = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

		faceCoords = self.faceCascade.detectMultiScale(grayImg, 1.5, 4)

		faces = []

		for coords in faceCoords:
			x,y,w,h = coords
			face = frame[y:y+h, x:x+w]
			faces.append(face)

		return faces

	def testDetection(self):
		cap = cv2.VideoCapture()
		while True:
			faces = self.detectFaces(cap.read()[1])
			if len(faces) > 0:
				print("face detected, punk")
			if cv2.waitKey(1) & 0xFF == ord('q'):
				break

	def trainFromDatabase(self, filter_threshold=3000):

		facedb = FaceDatabase(self.db)
		users = facedb.users()

		if not len(users):
			print("no users.  Not training.")
			return 0, 0

		i = 0
		faces = []
		ids = []
		self.users = []

		for user in users:
			self.users.append(user.userData)
			
			if not len(user.faceData):
				continue

			for faceData in user.faceData:
				if faceData["confidence"] > filter_threshold:
					continue
				data = base64.b64decode(faceData['face'])
				face = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
				face = cv2.resize(face, self.trainingSize)
				faces.append(face)
				ids.append(i)
			i+=1

		print("we have {} faces and {} ids".format(len(faces), len(ids)))


		if len(faces):
			self.recognizer.train(np.asarray(faces), np.asarray(ids, dtype=np.int32))

		return len(self.users), len(faces)

	def encodeImage(self, img):
		retval, data = cv2.imencode("foo.jpg", img)
		return base64.b64encode(data)


	def createUser(self, username, userFaces, level=1, realname=""):
		facedb = FaceDatabase(self.db)
		user, exists = facedb.insertUser(username, level, realname)

		for face, confidence in userFaces:
			if not face:
				continue

			data = self.encodeImage(face)
			if retval:
				facedb.insertFace(user['uuid'], data, confidence)

		facedb.db.commit()

		if not exists:
			self.users.append(user)

		return user

	def copyRow(self, row):
		obj = {}
		for key in row.keys():
			obj[key] = row[key]

		return obj

	def recognize(self, face):

		if not len(self.users):
			print("no users.  You must create users first")
			return None

		face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
		face = cv2.resize(face, self.trainingSize)
		faceId, confidence = self.recognizer.predict(face)
		user = None
		if faceId != -1:
			user = self.users[faceId]
			obj = self.getUsers(uuid = user["uuid"])[0]
			obj["confidence"] = confidence

			return obj

		return None

	def getUsers(self, filter=None, level=None, uuid=None):
		facedb = FaceDatabase(self.db)
		usersArray = []
		for user in self.users:
			if (filter and user["name"] != filter) or (level and user["level"] < level) or (uuid and user["uuid"] == uuid):
				continue
			obj = {}
			for k in user.keys():
				obj[k] = user[k];
			faces = facedb.facesForUser(user['uuid'])
			if len(faces):
				obj["face"] = str(faces[0]['face'])
			associations = facedb.associations(user['uuid'])
			obj["associations"] = associations

			usersArray.append(obj)
		debug("returning array of json strings of length: " + str(len(usersArray)))
		return usersArray

	def getUser(self, uuid):
		facedb = FaceDatabase(self.db)
		return self.copyRow(facedb.user(uuid))


	def addFaceToUser(self, uuid, face, confidence):
		face_data = self.encodeImage(face)
		facedb = FaceDatabase(self.db)
		facedb.insertFace(uuid, face_data, confidence)

	def addAssociation(self, uuid, associate_uuid):
		facedb = FaceDatabase(self.db)
		facedb.insertAssociation(uuid, associate_uuid)


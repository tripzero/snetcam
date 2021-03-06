#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os.path
try:
	from Crypto.Hash.SHA256 import SHA256Hash as sha256
except:
	from hashlib import sha256 

try:
	from rdrand import RdRandom
	random = RdRandom()
	print("using hardware rdrand random number generation")
except:
	try:
		from Crypto.Random import random
		print("using Crypto.Random for random number generation")

	except:
		import random
		print("using random.random for random number generation")


class FaceDatabase:

	FaceTableCreateStatement = 'CREATE TABLE Faces (id INTEGER PRIMARY KEY AUTOINCREMENT, uuid TEXT, face BLOB, age DATE DEFAULT CURRENT_DATE, confidence INTEGER)'
	UserTableCreateStatement = 'CREATE TABLE Users (username TEXT, uuid TEXT, level INTEGER, realname TEXT)'
	UserAuthTableCreateStatement = 'CREATE TABLE UserAuth (uuid TEXT, signature BLOB, bleuuid TEXT)'
	AssociationsTableCreateStatement = 'CREATE TABLE Associations (id INTEGER PRIMARY KEY AUTOINCREMENT, uuid TEXT, associate_uuid TEXT)'

	SelectUsersStatement = 'SELECT * FROM Users'
	SelectUsersWithLevel = 'SELECT * FROM Users WHERE level >= ?'
	SelectFaceForUserStatement = 'SELECT id,face,age,confidence FROM Faces WHERE uuid == ?'
	SelectSignatureStatement = 'SELECT signature FROM UserAuth WHERE uuid == ?'
	SelectUserAssociations = 'SELECT associate_uuid FROM Associations WHERE uuid == ?'
	UserAssociationsExists = 'SELECT uuid, associate_uuid FROM Associations WHERE uuid == ? and associate_uuid == ?'

	InsertUser = 'INSERT INTO Users (username, uuid, level, realname) VALUES(?,?,?,?)'
	InsertFace = 'INSERT INTO Faces (uuid, face, confidence) VALUES(?,?,?)'
	InsertUserSignature = 'INSERT INTO UserAuth (uuid, signature) VALUES(?,?)'
	InsertAssociation = 'INSERT INTO Associations (uuid, associate_uuid) VALUES(?,?)'

	DeleteFace = 'DELETE FROM Faces WHERE id=?'
	DeleteAssociation = "DELETE FROM Associations WHERE uuid=? AND associate_uuid=?"

	UpdateFaceUuid = "UPDATE Faces SET uuid = ? WHERE id == ?"
	UpdateFaceConfidence = "UPDATE Faces SET confidence = ? WHERE id == ?"
	UpdateUserLevel = "UPDATE Users SET level = ? WHERE uuid == ?"


	def __init__(self, db):
		create = False
		if db == ":memory:" or not os.path.isfile(db):
			create = True
		self.db = sqlite3.connect(db)
		self.db.row_factory = sqlite3.Row
		if create:
			self.createDatabase()

		self.logfile = open("FaceDatabase.log", "w")

	def debug(self, msg):
		self.logfile.write("{0}\n".format(msg))

	def __del__(self):
		print("closing db connection")
		self.db.close()

	def _users(self):
		rows = self.db.execute(FaceDatabase.SelectUsersStatement).fetchall()
		self.db.commit()
		return rows

	def facesForUser(self, uuid):
		rows = self.db.execute(FaceDatabase.SelectFaceForUserStatement,(uuid,)).fetchall()

		self.db.commit()
		self.debug("_facedForUser: " + str(len(rows)) + " rows found for user: " + str(uuid))
		return rows

	def createDatabase(self):
		self.db.execute(FaceDatabase.FaceTableCreateStatement)
		self.db.execute(FaceDatabase.UserTableCreateStatement)
		self.db.execute(FaceDatabase.UserAuthTableCreateStatement)
		self.db.execute(FaceDatabase.AssociationsTableCreateStatement)
		self.db.commit()

	def insertUser(self, username, level=1, realname=""):
		"""Return user and True if exists.  user and False if user does not exist"""

		user = self.db.execute("SELECT * FROM Users WHERE username == ?", (username,)).fetchone()

		if user != None and len(user):
			return user, True

		s = sha256()
		s.update(str(random.getrandbits(512)))
		uuid = s.hexdigest()

		print("creating user with uuid={}".format(uuid))
 
		self.db.execute(FaceDatabase.InsertUser, (username, uuid, level, realname,))
		self.db.commit()

		return self.user(uuid), False

	def insertAssociation(self, uuid, associate_uuid):

		cur = self.db.execute(FaceDatabase.UserAssociationsExists, (uuid, associate_uuid))

		if cur.rowcount >= 1:
			print("association already exists between {} and {}".format(uuid, associate_uuid))
			return

		self.db.execute(FaceDatabase.InsertAssociation, (uuid, associate_uuid))
		self.db.commit()

	def associations(self, uuid):
		cur = self.db.execute(FaceDatabase.SelectUserAssociations, (uuid,))

		rows = cur.fetchall()

		assc = []
		for row in rows:
			assc.append(row["associate_uuid"])

		return assc

	def removeAssociation(self, uuid, associate_uuid):
		return self.db.execute(FaceDatabase.DeleteAssociation, uuid, associate_uuid).rowcount >= 1


	def user(self, uuid):
		user = self.db.execute("SELECT * FROM Users WHERE uuid == ?", (uuid,)).fetchone()

		return user

	def user_by_username(self, username):
		user = self.db.execute("SELECT * FROM Users WHERE username == ?", (username,)).fetchone()

		return user

	def set_face_user_uuid(self, face_id, new_user_uuid):
		cur = self.db.cursor()
		cur.execute(FaceDatabase.UpdateFaceUuid, (new_user_uuid, face_id,))
		self.db.commit()

		return cur.rowcount == 1

	def set_face_confidence(self, face_id, confidence):
		cur = self.db.cursor()
		cur.execute(FaceDatabase.UpdateFaceConfidence, (confidence, face_id,))
		self.db.commit()

		return cur.rowcount == 1

	def set_user_level(self, uuid, level):
		cur = self.db.cursor()
		cur.execute(FaceDatabase.UpdateUserLevel, (level, uuid))
		self.db.commit()

		return cur.rowcount == 1

	def insertFace(self, uuid, face, confidence):
		self.db.execute(FaceDatabase.InsertFace, (uuid, face, confidence))
		self.db.commit()

	def deleteFace(self, id):
		self.db.execute(FaceDatabase.DeleteFace, (id,))
		self.db.commit()

	def users(self):
		users = self._users()
		theUsers = []
		for user in users:
			uuid = str(user['uuid'])
			print("uuid={}".format(uuid))
			theUsers.append(User(user, self.facesForUser(uuid), self.associations(uuid)))

		return theUsers

	def usersWithLevel(self, level):
		return self.db.execute(SelectUsersWithLevel, (level)).fetchall()

	def signature(self, uuid, sig = None):
		result = self.db.execute(FaceDatabase.SelectSignatureStatement, (uuid,)).fetchone()
		if result is None:
			#assume that this user has never authenticated
			if sig is None:
				return False
			self.db.execute(FaceDatabase.InsertUserSignature, (uuid, sig,))
			self.db.commit()
			return True

		print("db sig: ", result["signature"])
		print("sig: ", sig)
		if result["signature"] == sig:
			return True
		else:
			return False

class User:
	userData = None
	faceData = None
	associations = []

	def __init__(self, user, faces, associations):
		self.faceData = faces
		self.userData = user
		self.associations = associations




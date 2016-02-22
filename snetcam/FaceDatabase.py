#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import crypt
import os.path


class FaceDatabase:

	FaceTableCreateStatement = 'CREATE TABLE Faces (id INTEGER PRIMARY KEY AUTOINCREMENT, uuid TEXT, face BLOB, age DATE DEFAULT CURRENT_DATE)'
	UserTableCreateStatement = 'CREATE TABLE Users (username TEXT, uuid TEXT, level INTEGER, realname TEXT)'
	UserAuthTableCreateStatement = 'CREATE TABLE UserAuth (uuid TEXT, signature BLOB, bleuuid TEXT)'

	SelectUsersStatement = 'SELECT * FROM Users'
	SelectFaceForUserStatement = 'SELECT face,age FROM Faces WHERE uuid == ?'
	SelectSignatureStatement = 'SELECT signature FROM UserAuth WHERE uuid == ?'

	InsertUser = 'INSERT INTO Users (username, uuid, level, realname) VALUES(?,?,?,?)'
	InsertFace = 'INSERT INTO Faces (uuid, face) VALUES(?,?)'
	InsertUserSignature = 'INSERT INTO UserAuth (uuid, signature) VALUES(?,?)'


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
		self.db.close()

	def _users(self):
		rows = self.db.execute(FaceDatabase.SelectUsersStatement).fetchall()
		self.db.commit()
		return rows

	def _facesForUser(self, uuid):
		rows = self.db.execute(FaceDatabase.SelectFaceForUserStatement,(uuid,)).fetchall()

		self.db.commit()
		self.debug("_facedForUser: " + str(len(rows)) + " rows found for user: " + str(uuid))
		return rows

	def createDatabase(self):
		self.db.execute(FaceDatabase.FaceTableCreateStatement)
		self.db.execute(FaceDatabase.UserTableCreateStatement)
		self.db.execute(FaceDatabase.UserAuthTableCreateStatement)
		self.db.commit()

	def insertUser(self, username, level=1, realname=""):
		user = self.db.execute("SELECT * FROM Users WHERE username == ?", (username,)).fetchone()

		return -1

		uuid = crypt.crypt(username)
		self.db.execute(FaceDatabase.InsertUser, (username, uuid, level, realname,))
		self.db.commit()
		return uuid

	def user(self, uuid):
		user = self.db.execute("SELECT * FROM Users WHERE uuid == ?", (uuid,)).fetchone()

		return user

	def insertFace(self, uuid, face):
		self.db.execute(FaceDatabase.InsertFace, (uuid, face,))

	def users(self):
		users = self._users()
		theUsers = []
		for user in users:
			theUsers.append(User(user, self._facesForUser(user['uuid'])))

		return theUsers

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

	def __init__(self, user, faces):
		self.faceData = faces
		self.userData = user




#!/usr/bin/env python

from __future__ import print_function 
import cv2
import numpy as np
import trollius
import base64
import json
from binascii import hexlify
import sys, traceback
import argparse

import wssserver

usepympler = True

try:
	from pympler import tracker
except ImportError:
	usepympler = False

PY3 = sys.version_info[0] == 3

if PY3:
		xrange = range

class CameraServer(wssserver.Server):
	clients = []
	knownClients = {}
	broadcastRate = 10
	broadcastMsg = None
	fps = 30.0

	def __init__(self, hasFrameCb = None, fps = 30.0, port = 9001, usessl = True, sslcert = "server.crt", sslkey= "server.key", privateKeyFile = 'dhserver.key', clientsFile = "clients.json", loop = trollius.get_event_loop(), nopympler=True):
		wssserver.Server.__init__(self, port, usessl, sslcert, sslkey, privateKeyFile, clientsFile)
		self.loop = loop
		self.fps = fps
		self.hasFrame = hasFrameCb

		self.loop.create_task(self.broadcastLoop())
		self.loop.create_task(self.readCamera())
		
		if not nopympler:
			self.loop.create_task(self.tracker())

	@trollius.coroutine
	def tracker(self):
		if not usepympler:
			return

		tr = tracker.SummaryTracker()

		while True:
			tr.print_diff()
			yield trollius.From(trollius.sleep(10))
	
	def broadcast(self, msg):
		self.broadcastMsg = msg

	@trollius.coroutine
	def broadcastLoop(self):
		print("starting broadcast loop")
		try:
			
			if usepympler:
				tr = tracker.SummaryTracker()

			while True:
				try:
					if self.broadcastMsg is not None:
						success, data = cv2.imencode('.jpg', self.broadcastMsg)	
						data = np.getbuffer(data)
						msg = bytes(data)
						for c in self.clients:
							c.sendMessage(msg, True)
						del(data)				
				except: 
					pass
				finally:
					yield trollius.From(trollius.sleep(1/self.broadcastRate))
		except:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			traceback.print_exception(exc_type, exc_value, exc_traceback,
                          limit=2, file=sys.stdout)

	@trollius.coroutine
	def readCamera(self):
		cap = cv2.VideoCapture(0)
		frame = None
		success = False

		if not cap.isOpened():
			print("Failed to open camera!")
			return

		while True:
			try: 
				success, frame = cap.read()

				if not success:
					print("cap.read() failed")
					yield trollius.From(trollius.sleep(1.0/self.fps))
					continue
				
				self.broadcast(frame)

				if self.hasFrame:
					self.hasFrame(frame)

			except KeyboardInterrupt:
				self.loop.stop()

			except:
				exc_type, exc_value, exc_traceback = sys.exc_info()
				traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
				traceback.print_exception(exc_type, exc_value, exc_traceback,
	                          limit=2, file=sys.stdout)

			yield trollius.From(trollius.sleep(1.0/self.fps))

		cap.release()


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--ssl', dest="usessl", help="use ssl.", action='store_true')
	parser.add_argument('--sslcert', dest="sslcert", default="server.crt", nargs=1, help="ssl certificate")
	parser.add_argument('--sslkey', dest="sslkey", default="server.key", nargs=1, help="ssl key")

	args = parser.parse_args()

	usessl = args.usessl

	server = CameraServer(port=9000, usessl = usessl, sslcert=args.sslcert, sslkey = args.sslkey)

	loop = trollius.get_event_loop()
	

	print("starting server...")
	try:
		server.start()
		loop.run_forever()
	except KeyboardInterrupt:
		pass
	finally:
		loop.close()
#!/usr/bin/env python

from __future__ import print_function 
import cv2
import numpy as np
from autobahn.asyncio.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
import ssl
import trollius
import base64
import json
from binascii import hexlify
import sys, traceback
import argparse
from dh import DH

class Client:
	isAuthenticated = False

	def __init__(self, handle):
		self.handle = handle

	def sendMessage(self, msg, isBinary):
		if not self.isAuthenticated:
			return
		self.handle.sendMessage(msg, isBinary)

class Server:
	clients = []
	knownClients = {}
	broadcastRate = 10
	broadcastMsg = None

	def __init__(self, privateKeyFile = 'dhserver.key', clientsFile = "clients.json"):

		self.diffieHelmut = DH(privateKeyFile)
		try:
			with open(clientsFile) as cf:
				data = cf.read()
				self.knownClients = json.loads(data)
		except:
			print("exception while parsing {0}".format(clientsFile))
		self.secret = self.diffieHelmut.secret

		trollius.get_event_loop().create_task(self.broadcastLoop())
		trollius.get_event_loop().create_task(self.tracker())

	def registerClient(self, client):
		self.clients.append(Client(client))

	def hasClients(self):
		return len(self.clients)

	def broadcast(self, msg):	
		self.broadcastMsg = msg

	def unregisterClient(self, client):
		for c in self.clients:
			if c.handle == client:
				self.clients.remove(c)

	@trollius.coroutine
	def tracker(self):
		from pympler import tracker

		tr = tracker.SummaryTracker()

		while True:
			tr.print_diff()
			yield trollius.From(trollius.sleep(10))

	def authenticate(self, client, sharedSecret):
		#TODO: do real authentication
		for c in self.clients:
			if c.handle == client:
				symmetricKey = self.diffieHelmut.hashedSymmetricKey(sharedSecret)
				symmetricKey = hexlify(symmetricKey)
				
				if not sharedSecret in self.knownClients:
					if symmetricKey == self.knownClients[str(sharedSecret)]:
						c.isAuthenticated = True
						print("authentication success!")
					else:
						print("failed attempt to authenticate.  symmetric Key is wrong")
						print("symmetricKey: ", symmetricKey)
				else:
					print("failed attempt at authenticating.  shared secret is not in clients file")
					print("\"{0}\" : \"{1}\",".format(sharedSecret, symmetricKey))
					c.handle.close()
	
	@trollius.coroutine
	def broadcastLoop(self):
		print("starting broadcast loop")
		try:
			from pympler import tracker

			tr = tracker.SummaryTracker()
			while True:
				if self.broadcastMsg is not None:
					success, data = cv2.imencode('.jpg', self.broadcastMsg)
					data = np.getbuffer(data)
					msg = bytes(data)
					for c in self.clients:
						c.sendMessage(msg, True)
					del(data)
					
				
				yield trollius.From(trollius.sleep(1/self.broadcastRate))
		except:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			traceback.print_exception(exc_type, exc_value, exc_traceback,
                          limit=2, file=sys.stdout)

class MyServerProtocol(WebSocketServerProtocol):
	server = None

	def onConnect(self, request):
		print("Client connecting: {0}".format(request.peer))

	def onOpen(self):
		print("WebSocket connection open.")
		MyServerProtocol.server.registerClient(self)
		# send our shared secret:
		print("sending auth to client")
		payload = { "type" : "auth", "sharedSecret" : str(MyServerProtocol.server.diffieHelmut.sharedSecret) }
		payload = json.dumps(payload)
		self.sendMessage(payload, False)

	def onMessage(self, payload, isBinary):
		if isBinary:
			print("Binary message received: {0} bytes".format(len(payload)))
		else:
			print("Text message received: {0}".format(payload.decode('utf8')))
			msg = json.loads(payload.decode('utf8'))
			
			if 'sharedSecret' in msg and 'type' in msg and msg['type'] == 'auth':
				# {'type' : 'auth', 'sharedSecret' : 'key'}
				MyServerProtocol.server.authenticate(self, int(msg['sharedSecret']))

	def onClose(self, wasClean, code, reason):
		try:
			print("WebSocket connection closed: {0}".format(reason))
			MyServerProtocol.server.unregisterClient(self)
		except:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			traceback.print_exception(exc_type, exc_value, exc_traceback,
                          limit=2, file=sys.stdout)

@trollius.coroutine
def readCamera(cap):
	frame = None
	success = False

	if not cap.isOpened():
		print("Failed to open camera!")
		return

	while True:
		success, frame = cap.read()

		if not success:
			print("cap.read() failed")

		if MyServerProtocol.server.hasClients():
			#send encoded data to any clients
			MyServerProtocol.server.broadcast(frame)

		yield trollius.From(trollius.sleep(1.0/30.0))


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--ssl', dest="usessl", help="use ssl.", action='store_true')
	parser.add_argument('--sslcert', dest="sslcert", default="server.crt", nargs=1, help="ssl certificate")
	parser.add_argument('--sslkey', dest="sslkey", default="server.key", nargs=1, help="ssl key")
	args = parser.parse_args()

	usessl = args.usessl

	sslcontext = None

	if usessl:
		sslcontext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
		sslcontext.load_cert_chain(args.sslcert, args.sslkey)

	MyServerProtocol.server = Server()

	factory = WebSocketServerFactory(u"wss://127.0.0.1:9000", debug=False)
	factory.protocol = MyServerProtocol

	loop = trollius.get_event_loop()
	coro = loop.create_server(factory, '', 9000, ssl=sslcontext)
	server = loop.run_until_complete(coro)
	cap = cv2.VideoCapture(0)
	loop.create_task(readCamera(cap))

	print("starting server...")
	try:
		loop.run_forever()
	except KeyboardInterrupt:
		pass
	finally:
		server.close()
		loop.close()
		cap.close()
		broadcst.close()
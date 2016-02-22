from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory, connectWS
from twisted.internet import reactor
import json
import ssl
import cv2
import numpy as np
import traceback, sys
import base64
from dh import DH as DiffieHelmut

def debug(msg):
		print(msg)

class Client:
	handle = None

	def connectTo(self, addy, port, useSsl = True, hostname = None):
		debug("connectTo {0}:{1}".format(addy, port))
		self.address = addy
		self.port = port
		self.wsaddress = "wss://{0}:{1}".format(addy, port)
		self.hostname = hostname
		sslcontext = None

		if useSsl:
			from twisted.internet import ssl
			sslcontext = ssl.ClientContextFactory()

		factory = WebSocketClientFactory(self.wsaddress, debug=False, debugCodePaths=False)
		factory.protocol = MyClientProtocol
		connectWS(factory, sslcontext)

	def run(self, installSignalHandlers=0):
		reactor.run(installSignalHandlers)

	def setImgHandler(self, imgHandlerCallback):
		MyClientProtocol.imgHandlerCallback = imgHandlerCallback



class MyClientProtocol(WebSocketClientProtocol):
	imgHandlerCallback = None

	def __init__(self):
		WebSocketClientProtocol.__init__(self)
		self.diffieHelmut = DiffieHelmut('dhclient.key')

	def onConnect(self, response):
		print("Server connected: {0}".format(response.peer))

	def onOpen(self):
		print("WebSocket connection open.")

		Client.handle = self

		try:
			payload = { "type" : "auth", "sharedSecret" : str(self.diffieHelmut.sharedSecret) }
			payload = json.dumps(payload)
			print("trace", payload)
			print("sending auth to server")
			try:
				self.sendMessage(bytes(payload, 'utf8'), False)
			except:
				#probably on python2
				self.sendMessage(payload, False)
		except:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			traceback.print_exception(exc_type, exc_value, exc_traceback,
					limit=2, file=sys.stdout)

	def onMessage(self, payload, isBinary):
		if isBinary:
			try:
				img = np.frombuffer(payload, dtype='uint8')
				img = cv2.imdecode(img, cv2.IMREAD_COLOR)
				if self.imgHandlerCallback:
					foo = self.imgHandlerCallback
					foo(img)
			except KeyboardInterrupt:
				quit()
			except:
				exc_type, exc_value, exc_traceback = sys.exc_info()
				traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
				traceback.print_exception(exc_type, exc_value, exc_traceback,
						limit=2, file=sys.stdout)
		else:
			#TODO: authenticate the server
			pass

	def onClose(self, wasClean, code, reason):
		print("WebSocket connection closed: {0}".format(reason))

def displayImage(bleh, img):
	cv2.imshow("image", img)
	k = cv2.waitKey(1)

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('address', help="address", default="localhost", nargs="?")
	parser.add_argument('port', help="port", default=9000, nargs="?")
	parser.add_argument('--ssl', dest="usessl", help="use ssl.", action='store_true')
	args = parser.parse_args()

	client = Client()
	client.connectTo(args.address, args.port, useSsl=args.usessl)
	client.setImgHandler(displayImage)
	client.run(1)



from wss import Server
import trollius as asyncio
from datetime import datetime
import json
import sys, traceback
from imageresource import MINS

class WSResourceServer(Server):
	resources = []

	def __init__(self, pollRate = MINS(10), port=9001, sslcert = "server.crt", sslkey= "server.key", privateKeyFile = 'dhserver.key', clientsFile = "clients.json"):
		Server.__init__(self, True, port, sslcert, sslkey, privateKeyFile = privateKeyFile, clientsFile = clientsFile)
		self.pollRate = pollRate
		self.port = port

		self.numclients = len(self.clients)
		
		asyncio.get_event_loop().create_task(self.poll())

	def onMessage(self, msg, fromClient):
		print ("message received", msg)

		if msg["type"] == "method":
			deviceName = msg["deviceName"]
			callName = msg["method"]
			args = msg["args"]

			for call in Resource.callables:
				if deviceName in call and callName in call[deviceName]:
					c = call[deviceName][callName]
					try:
						c(*args)
					except:
						print("blew up while remotely calling: {0} on {1}".format(callName, deviceName))
				else:
					print("we have no registered method for: {0} on {1}".format(callName, deviceName))

		'''if msg["type"] == "subscribe":
			client = None

			for c in self.clients:
				if c.handle is fromClient:
					client = c

			subscription = msg["subscription"]
			resourceName = subscription["resourceName"]
			variableName = subscription["variable"]

			for resource in self.resources:
				if resource.name == resourceName and varianbleName in resource.variables:
					resource.subscribe(variableName, lambda value:
						msg = {"type" : "propertyChanged", "resourceName" : resource.name, "variableName" : variableName, "value" : value}
						if client:
							client.sendMessage(json.dumps(msg, False))
			'''

	def addResource(self, resource):
		self.resources.append(resource)

	@asyncio.coroutine
	def poll(self):
		print("WSResourceServer: poll()")

		rs = {}

		while True:
			try:
				rs = {}
				rs["resources"] = []

				for resource in self.resources:

					r = {}
					r["resourceName"] = resource.name
					r["variables"] = resource.variables
					r["lastUpdated"] = str(datetime.now())

					rs['resources'].append(r)

				self.broadcast(json.dumps(rs))

			except:
				exc_type, exc_value, exc_traceback = sys.exc_info()
				traceback.print_tb(exc_traceback, limit=2, file=sys.stdout)
				traceback.print_exception(exc_type, exc_value, exc_traceback,
                	          limit=6, file=sys.stdout)

			yield asyncio.From(asyncio.sleep(self.pollRate))





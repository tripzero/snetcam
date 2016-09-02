import cv2
import numpy as np
import traceback, sys
import trollius as asyncio
import base64

from wss import Client

def showImage(payload):
	payload = base64.b64decode(payload)
	img = np.frombuffer(payload, dtype='uint8')
	img = cv2.imdecode(img, cv2.IMREAD_COLOR)
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
	if client.connectTo(args.address, args.port, useSsl=args.usessl):
		print("Connected!")
	else:
		print("Failed to connect")
		
	client.setTextHandler(showImage)

	asyncio.get_event_loop().run_forever()


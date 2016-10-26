import trollius as asyncio
from snetcam.recognitionserver import RecognitionServer, WssCamera

if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('address', help="address", default="localhost", nargs="?")
	parser.add_argument('port', help="port", default=9000, nargs="?")
	parser.add_argument('--ssl', dest="usessl", help="use ssl.", action='store_true')
	parser.add_argument('--local', help="use local camera.", action='store_true')
	args = parser.parse_args()

	cam = None

	if args.local:
		cam = LocalCamera("test_cam")

	else:
		cam = WssCamera("wss_test_cam", args.address, args.port, args.usessl)

	serv = RecognitionServer([cam])

	asyncio.get_event_loop().run_forever()
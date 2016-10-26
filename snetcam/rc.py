import trollius as asyncio
from snetcam.recognitionclient import RecognitionClient, FaceRecognizedSignal, FaceDetectedSignal, ListUsersSignal, ErrorSignal, ListUsersWithLevelSignal

if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('address', help="address", default="localhost", nargs="?")
	parser.add_argument('port', help="port", default=9004, nargs="?")
	parser.add_argument('--ssl', dest="usessl", help="use ssl.", action='store_true')
	parser.add_argument('--camera_name', help="name of camera")
	args = parser.parse_args()

	client = RecognitionClient(args.camera_name, args.address, args.port, args.usessl)
	
	def connected():
		client.list_users()
		print("requesting users with level > 2...")
		print("")
		client.list_users_with_level(2)

	client.setOpenHandler(connected)

	def face_recognized(msg):
		print("face_recognized received: {}".format(msg.username))

	def face_detected(msg):
		print("face_recognized received: {}")

	def list_users(msg):
		print("users with level received")
		for user in msg.users:
			print("user: {}".format(user["username"]))

		print("")

	def list_users_with_level(msg):
		for user in msg.users:
			print("user: {}".format(user["username"]))

	def error_signal(msg):
		print("error: {}".format(msg.message))

	client.setMessageReceived(FaceRecognizedSignal, face_recognized)
	client.setMessageReceived(FaceDetectedSignal, face_detected)
	client.setMessageReceived(ListUsersSignal, list_users)
	client.setMessageReceived(ErrorSignal, error_signal)
	client.setMessageReceived(ListUsersWithLevelSignal, list_users_with_level)

	client.connect()

	asyncio.get_event_loop().run_forever()
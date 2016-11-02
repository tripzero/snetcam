import trollius as asyncio
from snetcam.recognitionserver2 import RecognitionServer
import rospy

if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('address', help="address", default="localhost", nargs="?")
	parser.add_argument('port', help="port", default=9000, nargs="?")
	parser.add_argument('--ssl', dest="usessl", help="use ssl.", action='store_true')
	parser.add_argument('--local', help="use local camera.", action='store_true')
	args = parser.parse_args()

	rospy.init_node('recognition_server', disable_signals=False)

	serv = RecognitionServer()

	print("{} users".format(len(serv.recognizer.users)))

	for user in serv.recognizer.users:
		print("username: {}, id: {}".format(user.username, user.uuid))

	asyncio.get_event_loop().call_later(60 * 5, serv.save_recognition_db)

	asyncio.get_event_loop().run_forever()
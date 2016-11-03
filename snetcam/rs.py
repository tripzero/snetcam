import trollius as asyncio
from snetcam.recognitionserver2 import RecognitionServer
import rospy

if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('--user_file', help="user_file", default="users.json", nargs="?")
	parser.add_argument('--recognition_db', help="recognition_db", default="recognition.db", nargs="?")
	args = parser.parse_args()

	rospy.init_node('recognition_server', disable_signals=False)

	serv = RecognitionServer(users_file=args.user_file, recognition_db=args.recognition_db)

	serv.load_recognition_db()

	print("{} users".format(len(serv.recognizer.users)))

	for user in serv.recognizer.users:
		print("username: {}, id: {}".format(user.username, user.uuid))

	asyncio.get_event_loop().call_later(60 * 5, serv.save_recognition_db)

	asyncio.get_event_loop().run_forever()
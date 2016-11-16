#!/usr/bin/env python

import trollius as asyncio
from recognizer import Recognizer
import rospy

if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('-o', dest="output_file", help="output_file", default=None)
	parser.add_argument('-i', dest="input_file", help="input_file", default=None)
	args = parser.parse_args()

	rospy.init_node('dumper', disable_signals=False)

	serv = Recognizer()

	if args.output_file:
		with open(args.output_file, "w+") as db:
			data = serv.serialize()
			db.write(data)

	elif args.input_file:
		with open(args.input_file, "r") as db:
			success = serv.deserialize(db.read())
			print("success: {}".format(success))

	rospy.signal_shutdown("Done")

#!/usr/bin/env python

import cv2
from .avg_color import color_filter
import numpy as np

def nothing(x):
	pass

if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument('file_to_process', help="file_to_process")
	
	args = parser.parse_args()
	
	img = cv2.imread(args.file_to_process, cv2.IMREAD_COLOR)

	if img is None:
		raise Exception("failed to read image")

	# Starting with 100's to prevent error while masking
	h,s,v = 100,100,100

	cv2.namedWindow('result')
	
	# Creating track bar
	cv2.createTrackbar('h', 'result',0, 179, nothing)
	cv2.createTrackbar('s', 'result',0, 255, nothing)
	cv2.createTrackbar('v', 'result',0, 255, nothing)

	cv2.imshow("original", img)

	upper = False
	upperhsv = (180, 255, 255)
	lowerhsv = (0, 0, 0)

	while(1):

		h = cv2.getTrackbarPos('h','result')
		s = cv2.getTrackbarPos('s','result')
		v = cv2.getTrackbarPos('v','result')

		if upper:
			result = color_filter(img, lowerhsv, (h, s, v))
		else:
			result = color_filter(img, (h, s, v), upperhsv)

		cv2.imshow("result", result)

		k = cv2.waitKey(5) & 0xFF
		if k == 27:
			break
		elif k == 24:
			if upper:
				upperhsv = (h, s, v)
				print("upper hsv: {}".format(upperhsv))
			else:
				lowerhsv = (h, s, v)
				print("lower hsv: {}".format(lowerhsv))


	cv2.destroyAllWindows()

# Creating a window for later use




#!/usr/bin/env python

from imageresource import *
import cv2
import trollius as asyncio

def color_filter(img, color_hsv_lower, color_hsv_upper):
	hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

	mask = cv2.inRange(hsv, color_hsv_lower, color_hsv_upper)
	res = cv2.bitwise_and(img, img, mask = mask)

	return res

class AverageColor(MultiprocessImageResource):

	def __init__(self, color_filter_val=None):
		self.color_filter_val = color_filter_val
		MultiprocessImageResource.__init__(self, "avg_color", 2, maxQueueSize=4)

	def process(self):
		while True:
			img = self.dataQueue.get()

			img = dataToImage(img, True)

			if self.color_filter_val is not None:
				img = color_filter(img, self.color_filter_val[0], self.color_filter_val[1])

			result = cv2.mean(img)

			self.resultQueue.put(result)

	def hasResult(self, result):
		self.setValue("color", result)

@asyncio.coroutine
def showImage(avgColor):
	cap = cv2.VideoCapture(0)

	while True:

		ret, img = cap.read()

		if not ret:
			break

		avgColor.handleImg(img)

		cv2.imshow("image", img)
		k = cv2.waitKey(1)

		print("has image!")

		yield asyncio.From(asyncio.sleep(1/30))

if __name__ == '__main__':
	import argparse
	from wss import Client

	parser = argparse.ArgumentParser()
	args = parser.parse_args()

	client = Client()

	avgColor = AverageColor()


	asyncio.get_event_loop().create_task(showImage(avgColor))

	asyncio.get_event_loop().run_forever()			

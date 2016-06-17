#!/usr/bin/env python

from imageresource import *
import cv2
import trollius as asyncio

class AverageColor(MultiprocessImageResource):

	def __init__(self):
		MultiprocessImageResource.__init__(self, 2, maxQueueSize=4)

	def process(self):
		while True:
			img = self.dataQueue.get()		
			
			result = cv2.mean(img)

			self.resultQueue.put(result)

	def hasResult(self, result):
		print(result)

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
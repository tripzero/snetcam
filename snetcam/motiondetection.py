from imageresource import MultiprocessImageResource, dataToImage, imgToData
import cv2
import numpy as np
import sys
import os
import traceback
from datetime import datetime

class FakeOutput:
	msg=""
	def write(self, msg):
		self.msg += "\n" + msg

class MotionDetect(MultiprocessImageResource):

	def __init__(self, name, processes=1):
		MultiprocessImageResource.__init__(self, name, processes=processes)

	def hasResult(self, result):
		#print("queue size: {0}".format(self.dataQueue.qsize()))
		#print("result queue: {0}".format(self.resultQueue.qsize()))
		hasMotion, imgData = result[:]
		self.setValue("motionDetected", hasMotion)

		if hasMotion:
			frame = dataToImage(imgData, True)
			#cv2.imshow("motion detected", frame)
			#cv2.waitKey(1)
			self.setValue("lastMotionDetected", str(datetime.now()))



	def process(self):
		self.debugOut("process forked and started!")
		frame1 = None
		frame2 = None
		frame3 = None
		maxDeviation = 200
		minDeviation = 40

		while True:
			imgData = self.dataQueue.get()
			try:
				frame = dataToImage(imgData, True)
				cv2.imshow("motion detected", frame)
				cv2.waitKey(1)
				#frame = cv2.pyrDown(frame)
				#frame = cv2.pyrDown(frame)

				if frame1 == None:
					frame1 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
					continue
				if frame2 == None:
					frame2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
					continue

				frame1 = frame2
				frame2 = frame3
				frame3 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

				d1 = cv2.absdiff(frame1, frame3)
				d2 = cv2.absdiff(frame3, frame2)
				motion = cv2.bitwise_and(d1, d2)
				ret, motion = cv2.threshold(motion, 20, 255, cv2.THRESH_BINARY)
				#motion = cv2.erode(motion, kernel_ero, iterations = 1)
				mean, stddev = cv2.meanStdDev(motion)

				stddev = stddev[0]

				if  stddev > minDeviation and stddev < maxDeviation:
					image, contours, heirarchy = cv2.findContours(motion, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
					if len(contours) > 0:
						self.debugOut("stddev = {0}".format(stddev))
						width, height, layers = frame.shape
						cv2.drawContours(frame, contours, -1, (0, 0, 255), 5)
						data = imgToData(frame, True)
						self.debugOut("putting image")
						self.resultQueue.put((True, data))
				else:
					#self.debug("no motion for this frame: {0}".format(stddev[0]))
					self.resultQueue.put((False, None))

			except KeyboardInterrupt:
				return
				
			except:
				self.debugOut("motion detect error!")
				fakeOutput = FakeOutput()
				exc_type, exc_value, exc_traceback = sys.exc_info()
				traceback.print_tb(exc_traceback, limit=4, file=fakeOutput)
				traceback.print_exception(exc_type, exc_value, exc_traceback,
		                        limit=10, file=fakeOutput)
				self.debugOut(fakeOutput.msg)
				#return

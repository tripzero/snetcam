from .imageresource import MultiprocessImageResource, dataToImage, DeQueue

import cv2
import numpy as np
import trollius as asyncio
from datetime import datetime, timedelta
import traceback, sys
from Queue import Empty

def HOURS(h):
	return h * 3600

def DAYS(d):
	return HOURS(d * 24)

def MINS(m):
	return m * 60

class TimeLapseRecorder(MultiprocessImageResource):

	def __init__(self, startTime=datetime.now().time(), interval=HOURS(24), length=DAYS(7), fps=30.0, outputfile="timelapse"):
		MultiprocessImageResource.__init__(self, "timelapse", processes=1, maxQueueSize=1, args=(startTime, interval, length, fps, outputfile,))

		self.startTime = startTime
		self.interval = interval
		self.length = length
		self.fps = fps
		self.outputFile = outputfile

	def startVideo(self):
		fourcc = cv2.VideoWriter_fourcc(*'XVID')
		self.videoDate = datetime.now() + timedelta(seconds=self.length)
		self.video = cv2.VideoWriter('{0}-{1}.m4v'.format(self.outputFile, self.videoDate), fourcc, self.fps, (640, 480))

	def process(self, startTime, interval, length, fps, outputfile):
		self.startTime = startTime
		self.interval = interval
		self.length = length
		self.fps = fps
		self.outputFile = outputfile

		self.startVideo()
		loop = asyncio.get_event_loop()
		loop.create_task(self.record())
		loop.run_forever()

	@asyncio.coroutine
	def record(self):
		try:
			t1 = datetime.now().time().hour

			t2 = self.startTime.hour

			if t1 < t2:
				wait = HOURS(t2-t1)
				self.debugOut("waiting for {0} seconds to start...".format(wait))
				yield asyncio.From(asyncio.sleep(wait))

			self.startedTime = datetime.now()
			self.debugOut("starting time lapse video")

			while True:
				try:
					imgData = self.dataQueue.get(False)
					img = dataToImage(imgData, True)
					height, width, layers = img.shape
					cv2.putText(img, "date: {0}".format(datetime.now()), (0, height-20), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255))

					for i in xrange(self.fps):
						self.video.write(img)
						cv2.waitKey(1)
						yield asyncio.From(asyncio.sleep(1/self.fps))

				except Empty:
					pass

				if self.videoDate <= datetime.now():
					self.debugOut("finalizing time lapse video")
					self.video.release()
					self.startVideo()

				yield asyncio.From(asyncio.sleep(self.interval))

		except KeyboardInterrupt:
			self.video.release()

		except:
			class FakeOutput:
				msg=""
				def write(self, msg):
					self.msg += "\n" + msg

			fakeout = FakeOutput()
			self.debugOut("recording crashed!!")
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=4, file=fakeout)
			traceback.print_exception(exc_type, exc_value, exc_traceback,
	                        limit=10, file=fakeout)
			self.debugOut(fakeout.msg)

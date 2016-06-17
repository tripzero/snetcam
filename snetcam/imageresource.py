import cv2
import numpy as np
import json
import base64
from collections import deque
import trollius as asyncio
import sys, os, traceback
from multiprocessing import Process, Queue, Pool
from Queue import Empty

def MINS(mins):
	return mins * 60

def dataToImage(data, base64Encode = False):
	if base64Encode:
		data = base64.b64decode(data)
	img = np.frombuffer(data, dtype='uint8')
	img = cv2.imdecode(img, cv2.IMREAD_COLOR)
	return img

def imgToData(frame, base64Encode = False):
	success, data = cv2.imencode('.jpg', frame)
	assert success
	data = np.getbuffer(data)
	if base64Encode:
		data = base64.b64encode(data)
	return data

class DeQueue(object):
	def __init__(self, size=None):
		self.maxSize = size
		self.queue = Queue()

	def put(self, data, block=True, timeout=None):
		try:
			if self.maxSize and self.qsize() >= self.maxSize:
				'pop off'
				self.queue.get(False)
		except Empty:
			pass
		return self.queue.put(data, block, timeout)

	def get(self, block=True, timeout=None):
		return self.queue.get(block, timeout)

	def get_nowait(self):
		return self.queue.get(False)

	def qsize(self):
		return self.queue.qsize()


class MultiprocessImageResource():
	pollRate = 0.001
	debug = False

	def __init__(self, processes=1, maxQueueSize=100, args=None):
		try:
			self.pool = []
			self.resultQueue = DeQueue(maxQueueSize)
			self.dataQueue = DeQueue(maxQueueSize)
			self.debugQueue = Queue()

			for i in range(processes):
				if args:
					p = Process(target=self.process, args=args)
				else:
					p = Process(target=self.process)
				self.pool.append(p)
				p.start()

			asyncio.get_event_loop().create_task(self.poll())

		except:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			traceback.print_exception(exc_type, exc_value, exc_traceback,
            	          limit=2, file=sys.stdout)

	def __del__(self):
		for process in self.pool:
			process.terminate()
			process.join()

	def debugOut(self, msg):
		#if self.debug:
		self.debugQueue.put(msg)

	def handleImg(self, data):
		self.dataQueue.put(data)

	@asyncio.coroutine
	def poll(self):
		print("poll task started")

		while True:
			try:
				msg = self.debugQueue.get_nowait()
				print(msg)
				
			except Empty:
				pass

			except:
				exc_type, exc_value, exc_traceback = sys.exc_info()
				print("poll exception")
				traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
				traceback.print_exception(exc_type, exc_value, exc_traceback,
                	          limit=2, file=sys.stdout)
			try:
				result = self.resultQueue.get_nowait()
				self.hasResult(result)
				
			except Empty:
				pass

			except:
				exc_type, exc_value, exc_traceback = sys.exc_info()
				print("poll exception")
				traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
				traceback.print_exception(exc_type, exc_value, exc_traceback,
                	          limit=2, file=sys.stdout)
			finally:
				yield asyncio.From(asyncio.sleep(self.pollRate))

	"""
	Should be overriden in subclass.  For example:
	def process(self):
		while True:
			imgData = self.dataQueue.get()
			img = dataToImage(imgData)
			# Do processing...
			self.resultQueue.put(result)
	"""
	def process(self):
		print ("base process() is being called.  You should have overridden this")
		assert False

	"""
	Should be overriden in subclass.  This will be called when a result is processed from the 
	result queue.
	"""
	def hasResult(self, result):
		print("you need to implement 'hasResult' in your subclass")
		assert False

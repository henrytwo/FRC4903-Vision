#pip3 install opencv-python
#sudo apt install libopencv-dev python3-opencv
#sudo apt install libopencv-dev python-opencv

#Instructions for installing on pi
#pip3 install opencv-python
#sudo apt-get install libcblas-dev
#sudo apt-get install libhdf5-dev
#sudo apt-get install libhdf5-serial-dev
#sudo apt-get install libatlas-base-dev
#sudo apt-get install libjasper-dev
#sudo apt-get install libqtgui4
#sudo apt-get install libqt4-test

import cv2
import glob
import numpy as np
from PIL import Image
from http.server import BaseHTTPRequestHandler,HTTPServer
from socketserver import ThreadingMixIn
from io import BytesIO
import os
import time
import datetime

try:
	from gpiozero import LED

	ON_PI = True
except:
	ON_PI = False
	print('This is not a pi.')

import subprocess

while ON_PI and not b'10.49.3.10' in subprocess.Popen(['ifconfig'], stdout=subprocess.PIPE).communicate()[0]:
	time.sleep(1)
	print('Waiting for network...')

if b'10.49.3.10' in subprocess.Popen(['ifconfig'], stdout=subprocess.PIPE).communicate()[0]:
	HOST = '10.49.3.10'
else:
	HOST = '127.0.0.1'

PORT = 80

CAM_DRIVE = 0 #'/dev/v4l/by-path/pci-0000:00:14.0-usb-0:2:1.0-video-index0'
CAM_MECH = '/dev/v4l/by-path/pci-0000:00:14.0-usb-0:1:1.0-video-index0'
CAM_LINE = '/dev/v4l/by-path/pci-0000:00:14.0-usb-0:3:1.0-video-index0'

class CamHandler(BaseHTTPRequestHandler):
	def do_GET(self):

		print(self.path)

		if self.path == '/reboot':
			self.send_response(200)
			self.send_header('Content-type', 'text/html')
			self.end_headers()
			self.wfile.write(b'ok')

			os.system('sudo reboot')

		elif self.path.endswith('.mjpg'):

			frame_name = int(self.path[1:].split('.mjpg')[0])

			if 0 <= frame_name < len(frames):

				self.send_response(200)
				self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
				self.end_headers()
				while True:
					try:
						img = frames[frame_name]()

						imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

						#imgRGB=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)

						jpg = Image.fromarray(imgRGB)

						with BytesIO() as output:
							jpg.save(output, format='JPEG')

							self.wfile.write(b"--jpgboundary")
							self.send_header('Content-type','image/jpeg')
							self.send_header('Content-length',str(len(output.getvalue())))
							self.end_headers()

							jpg.save(self.wfile, format='JPEG')

							time.sleep(0.01)
					except KeyboardInterrupt:
						break


			self.send_response(404)
			self.send_header('Content-type', 'text/html')
			self.end_headers()

			return

		elif 'public' + self.path in glob.glob('public/*'):

			with open('public' + self.path, 'r') as file:

				self.send_response(200)
				self.send_header('Content-type', 'text/js')
				self.end_headers()
				self.wfile.write(file.read().encode())

				return

		else:
			main_page = open('views/index.html', 'r').read()
			cam_page = open('views/cam.html', 'r').read()

			primary_page = open('views/primary.html', 'r').read()
			secondary_page = open('views/secondary.html', 'r').read()

			# CINRGY HARDCODE INCOMMING

			#, CAM2=cam_page_template.format(MACHINENAME='2', PORT=PORT, HOST=HOST)

			if self.path == '/secondary':
				print('Secondary frame injection')

				frame = secondary_page.format(CAM2=cam_page.format(MACHINENAME='2', PORT=PORT, HOST=HOST))

			else:
				print('Primary frame injection')

				frame = primary_page.format(CAM0=cam_page.format(MACHINENAME='0', PORT=PORT, HOST=HOST), CAM1=cam_page.format(MACHINENAME='1', PORT=PORT, HOST=HOST))

			page = main_page.format(FRAME=frame).encode()

			self.send_response(200)
			self.send_header('Content-type','text/html')
			self.end_headers()
			self.wfile.write(page)
			return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	pass

class TeleopCam:
	def __init__(self, id, w, h, enforced, rotation, points):
		self.id = id
		self.enforced = enforced
		self.w = w
		self.h = h
		self.rotation = rotation
		self.points = points

		self.capture = cv2.VideoCapture(self.id)

		if not self.enforced:
			self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, w)
			self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
		else:

			print('Enforcing resolution')

			self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, enforced[0])
			self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, enforced[1])

	def getFrame(self):
		rc, img = self.capture.read()

		if self.enforced:
			img = cv2.resize(img, (self.w, self.h))

		if self.rotation == 90:
			img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
		elif self.rotation == 180:
			img = cv2.rotate(img, cv2.ROTATE_180)

		if self.points:

			if self.rotation == 90:
				w = self.h
				h = self.w
			else:
				w = self.w
				h = self.h

			for point in self.points:
				cv2.line(img, (int(point[0][0] * w), int(point[0][1] * h)), (int(point[1][0] * w), int(point[1][1] * h)), (0, 0, 255), 1)

		return img

#(int(self.w * 0.55), 0), (int(self.w * 0.56), self.h)

primaryCam = TeleopCam(CAM_DRIVE, int(683 * 0.30), int(384 * 0.30), (int(683 * 0.65), int(384 * 0.65)), 180, [[(0.55, 0), (0.56, 1)]])
mechCam = TeleopCam(CAM_MECH, int(683 * 0.30), int(384 * 0.30), (int(683 * 0.65), int(384 * 0.65)), 90, [[(0, 0.07), (1, 0.07)], [(0, 0.655), (1, 0.655)]])
#lineCam = TeleopCam(CAM_LINE, int(683 * 0.30), int(384 * 0.30), (int(683 * 0.65), int(384 * 0.65)), False)

if __name__ == '__main__':

	frames = [mechCam.getFrame, primaryCam.getFrame] #, primaryCam.getFrame]

	try:
		server = ThreadedHTTPServer((HOST, PORT), CamHandler)
		print("Server started @ (%s:%i)" % (HOST, PORT))
		server.serve_forever()
	except KeyboardInterrupt:
		# capture.release()
		# capture.release()
		server.socket.close()
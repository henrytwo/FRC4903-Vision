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
from PIL import Image
from http.server import BaseHTTPRequestHandler,HTTPServer
from socketserver import ThreadingMixIn
from io import BytesIO
import os
import time
import datetime

from AutoTarget import *
import subprocess

if b'10.49.3.10' in subprocess.Popen(['ifconfig'], stdout=subprocess.PIPE).communicate()[0]:
	HOST = '10.49.3.10'
else:
	HOST = '127.0.0.1'

PORT = 8080

CAM_DRIVE = '/dev/v4l/by-id/usb-Guillemot_Corporation_USB_Camera-video-index0' #0 #'/dev/v4l/by-id/usb-HD_Camera_Manufacturer_USB_2.0_Camera-video-index0'
CAM_MECH = '/dev/v4l/by-id/usb-SunplusIT_INC._Integrated_Camera-video-index1' #1 #'/dev/v4l/by-id/usb-046d_Logitech_Webcam_C930e_74B595EE-video-index0'

vert = ['primaryFrame', 'mechFrame']

class CamHandler(BaseHTTPRequestHandler):
	def do_GET(self):

		print(self.path)

		if self.path == '/reboot':
			self.send_response(200)
			self.send_header('Content-type', 'text/html')
			self.end_headers()
			self.wfile.write('ok')

			os.system('sudo reboot')


		elif self.path == '/flip':
			vert.append(vert[0])
			del vert[0]

			self.send_response(200)
			self.send_header('Content-type', 'text/html')
			self.end_headers()
			self.wfile.write('ok')

		elif self.path.endswith('.mjpg'):

			frame_name = self.path[1:].split('.mjpg')[0]

			if frame_name in frames:

				self.send_response(200)
				self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
				self.end_headers()
				while True:
					try:
						img = frames[frame_name]['frame']()

						if vert[0] == frame_name:
							img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

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
			with open('index.html', 'r') as main_page:

				with open('cam.html', 'r') as cam_page:

					cams = ''
					cam_page_template = cam_page.read()

					for camName in frames:
						cams += cam_page_template.format(MACHINENAME=camName, PORT=PORT, HOST=HOST)

					page = main_page.read().format(CAMS=cams).encode()

					self.send_response(200)
					self.send_header('Content-type','text/html')
					self.end_headers()
					self.wfile.write(page)
					return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	pass

class TeleopCam:
	def __init__(self, id, w, h, enforced):
		self.id = id
		self.enforced = enforced
		self.w = w
		self.h = h

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

		#cv2.putText(img, str(datetime.datetime.now()),
		#			(10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.3,
		#			(255, 255, 255), 1, cv2.LINE_AA)

		return img

primaryCam = TeleopCam(CAM_DRIVE, int(683 * 0.30), int(384 * 0.30), (int(683 * 0.65), int(384 * 0.65)))
mechCam = TeleopCam(CAM_MECH, int(683 * 0.30), int(384 * 0.30), (int(683 * 0.65), int(384 * 0.65)))

if __name__ == '__main__':

	frames = {
		'primaryFrame': {
			'frame': primaryCam.getFrame,
			'humanName': 'Teleop Raw Feed'
		},
		'mechFrame': {
			'frame': primaryCam.getFrame,
			'humanName': 'Other stuff Feed'
		}
	}


	try:
		server = ThreadedHTTPServer((HOST, PORT), CamHandler)
		print("Server started @ (%s:%i)" % (HOST, PORT))
		server.serve_forever()
	except KeyboardInterrupt:
		# capture.release()
		# capture.release()
		server.socket.close()
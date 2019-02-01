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
from PIL import Image
from http.server import BaseHTTPRequestHandler,HTTPServer
from socketserver import ThreadingMixIn
from io import BytesIO
import time
import datetime

from AutoTarget import *

capture=None

HOST = '127.0.0.1'
PORT = 8080

CAM_AUTO = 2
CAM_TELEOP = 0

class CamHandler(BaseHTTPRequestHandler):
	def do_GET(self):

		print(self.path)

		if self.path.endswith('.mjpg'):

			frame_name = self.path[1:].split('.mjpg')[0]

			if frame_name in frames:

				self.send_response(200)
				self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
				self.end_headers()
				while True:
					try:
						img = frames[frame_name]['frame']()

						imgRGB=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
						jpg = Image.fromarray(imgRGB)

						with BytesIO() as output:
							jpg.save(output, format='JPEG')

							self.wfile.write(b"--jpgboundary")
							self.send_header('Content-type','image/jpeg')
							self.send_header('Content-length',str(len(output.getvalue())))
							self.end_headers()

							jpg.save(self.wfile, format='JPEG')

							time.sleep(0.05)
					except KeyboardInterrupt:
						break

			else:
				print('no u')

			self.send_response(404)
			self.send_header('Content-type', 'text/html')
			self.end_headers()

			return
		else:
			with open('index.html', 'r') as main_page:

				with open('cam.html', 'r') as cam_page:

					cams = ''
					cam_page_template = cam_page.read()

					for camName in frames:
						cams += cam_page_template.format(MACHINENAME=camName, PORT=PORT, HOST=HOST, HUMANNAME=frames[camName]['humanName'])

					page = main_page.read().format(CAMS=cams).encode()

					self.send_response(200)
					self.send_header('Content-type','text/html')
					self.end_headers()
					self.wfile.write(page)
					return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	pass

def teleopFrame():
	rc, img = capture.read()

	cv2.putText(img, str(datetime.datetime.now()),
				(10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.3,
				(255, 255, 255), 1, cv2.LINE_AA)

	return img

def main():
	global capture, frames
	capture = cv2.VideoCapture(CAM_TELEOP)
	capture.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
	capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

	at = AutoTarget(False, CAM_AUTO)

	frames = {
		'teleopFrame':  {
			'frame': teleopFrame,
			'humanName': 'Teleop Raw Feed'
		},
		'autoFrame': {
			'frame': at.get_frame,
			'humanName': 'CV Raw Feed'
		},
		'autoMask': {
			'frame': at.get_mask,
			'humanName': 'CV Mask'
		},
		'autoRes':  {
			'frame': at.get_res,
			'humanName': 'CV Overlay'
		}
	}

	try:
		server = ThreadedHTTPServer((HOST, PORT), CamHandler)
		print("Server started @ (%s:%i)" % (HOST, PORT))
		server.serve_forever()
	except KeyboardInterrupt:
		capture.release()
		server.socket.close()

if __name__ == '__main__':
	main()

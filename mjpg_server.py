#!/usr/bin/python
'''
	Author: Igor Maculan - n3wtron@gmail.com
	A Simple mjpg stream http server
'''
import cv2
from PIL import Image
import threading
from http.server import BaseHTTPRequestHandler,HTTPServer
from socketserver import ThreadingMixIn
#from io import StringIO
from io import BytesIO
import time
import datetime
capture=None

HOST = '192.168.0.141'
PORT = 8080

class CamHandler(BaseHTTPRequestHandler):
	def do_GET(self):

		if self.path.endswith('.mjpg'):
			self.send_response(200)
			self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
			self.end_headers()
			while True:
				try:
					rc,img = capture.read()

					cv2.putText(img, str(datetime.datetime.now()),
								(10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.3,
								(255, 255, 255), 1, cv2.LINE_AA)

					if not rc:
						continue
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
			return
		else:
			with open('index.html', 'r') as file:
				page = file.read().format(HOST=HOST, PORT=PORT).encode()

				self.send_response(200)
				self.send_header('Content-type','text/html')
				self.end_headers()
				self.wfile.write(page)
				return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	"""Handle requests in a separate thread."""

def main():
	global capture
	capture = cv2.VideoCapture(0)
	capture.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
	capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

	try:
		server = ThreadedHTTPServer((HOST, PORT), CamHandler)
		print("server started")
		server.serve_forever()
	except KeyboardInterrupt:
		capture.release()
		server.socket.close()

if __name__ == '__main__':
	main()

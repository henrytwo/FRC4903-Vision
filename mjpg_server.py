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
capture=None

class CamHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		#print('lol?', self.path)
		if self.path.endswith('.mjpg'):
			self.send_response(200)
			self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
			self.end_headers()
			while True:
				try:
					rc,img = capture.read()

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
		if self.path.endswith('.html'):
			self.send_response(200)
			self.send_header('Content-type','text/html')
			self.end_headers()
			self.wfile.write(b'<html><head></head><body>lol')
			self.wfile.write(b'<img src="http://192.168.0.141:8080/cam.mjpg" style="width: 100vw; height: auto;"/>')
			self.wfile.write(b'</body></html>')
			return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	"""Handle requests in a separate thread."""

def main():
	global capture
	capture = cv2.VideoCapture(0)
	capture.set(cv2.CAP_PROP_FRAME_WIDTH, 320);
	capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 240);
	#capture.set(cv2.cv.CV_CAP_PROP_SATURATION,0.2);
	global img

	try:
		server = ThreadedHTTPServer(('192.168.0.141', 8080), CamHandler)
		print("server started")
		server.serve_forever()
	except KeyboardInterrupt:
		capture.release()
		server.socket.close()

if __name__ == '__main__':
	main()

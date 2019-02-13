import cv2
import numpy as np
import traceback
import threading
import time
import sys
import os
import math

from networktables import NetworkTables
import logging

class AutoTarget:
    def __init__(self, headless, camID):
        self.cap = cv2.VideoCapture(camID)
        self.headless = headless
        self.FOV = 70

        self.WIDTH = 640 #320 #1024
        self.HEIGHT = 480 #240 #615

        self.Y_DEVIATION = 100
        self.X_DEVIATION = 200

        self.TARGET_RATIO = 14.5/6

        self.frame = np.ones((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)
        self.mask = np.ones((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)
        self.res = np.ones((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)

        NetworkTables.initialize(server='localhost')
        #NetworkTables.addEntryListener(changeListener)
        self.table = NetworkTables.getTable("Vision")

        logging.basicConfig(level=logging.DEBUG)

        self.table.putNumber('locked', 0)
        self.table.putNumber('heading', 0)
        self.table.putNumber('deviation', 0)
        self.table.putNumber('lastUpdated', -1)

        cv2.putText(self.frame, 'No signal',
                    (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                    (255, 255, 255), 1, cv2.LINE_AA)

        cv2.putText(self.mask, 'No signal',
                    (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                    (255, 255, 255), 1, cv2.LINE_AA)

        cv2.putText(self.res, 'No signal',
                    (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                    (255, 255, 255), 1, cv2.LINE_AA)

        os.system('v4l2-ctl -d %i -c white_balance_temperature_auto=0' % camID)
        os.system('v4l2-ctl -d %i -c white_balance_temperature=0' % camID)
        os.system('v4l2-ctl -d %i -c saturation=100' % camID)
        os.system('v4l2-ctl -d %i -c contrast=100' % camID)
        os.system('v4l2-ctl -d %i -c exposure_auto=1' % camID)
        os.system('v4l2-ctl -d %i -c exposure_absolute=0' % camID)
        os.system('v4l2-ctl -d %i -c brightness=50' % camID)

        print('Cam ID %i succeeded' % camID)

        #self.cap.set(3, self.W)
        #self.cap.set(4, self.H)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.HEIGHT)

        #self.HEIGHT, self.WIDTH, _ = self.cap.read()[1].shape

        self.upper_thresh = np.array([255, 255, 255])
        #self.upper_thresh = np.array([103, 255, 255])
        self.lower_thresh = np.array([0, 0, 112])
        #self.lower_thresh = np.array([75, 255, 120])

        threading.Thread(target=self.run, args=()).start()

    def get_frame(self):
        return self.frame

    def get_mask(self):
        return cv2.cvtColor(self.mask,cv2.COLOR_GRAY2RGB)

    def get_res(self):
        return self.res

    def run(self):
        while True:

            self.frame = self.cap.read()[1]

            # Convert to HSV
            hsv = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)

            # Create mask
            self.mask = cv2.inRange(hsv, self.lower_thresh, self.upper_thresh)

            im2, cnts, hierarchy = cv2.findContours(self.mask.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

            rects = []

            left = []
            right = []

            best_group = [(-1, -1, -1, -1), 0, 0]
            min_deviation = 999999

            for c in cnts:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.02 * peri, True)
                x, y, w, h = cv2.boundingRect(approx)

                approx = list(approx)

                approx.append(approx[0])

                longest = -1
                longest_coords = []

                if h >= 10 and w >= 3:
                    rect = (x, y, w, h)
                    rects.append(rect)

                    if abs(len(approx) - 4) <= 5:
                        points = [x + w // 2, y + h // 2, x, y, w, h, len(approx)]

                        if not self.headless:

                            prev = ()

                            count = 0

                            if not self.headless:
                                cv2.putText(self.frame,
                                            'Num sides: %i' % (len(approx)),
                                            (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                                            (255, 255, 255), 1, cv2.LINE_AA)

                            for i in approx:
                                if prev:

                                    if math.hypot(i[0][0] - prev[0], i[0][1] - prev[1]) > longest:
                                        longest = math.hypot(i[0][0] - prev[0], i[0][1] - prev[1])
                                        longest_coords = [prev, (i[0][0], i[0][1])]

                                    cv2.line(self.frame, prev, (i[0][0], i[0][1]), (0, 0, 255), 1)

                                prev = (i[0][0], i[0][1])

                                count += 1

                                if not self.headless:

                                    cv2.putText(self.frame,
                                                '%i' % (count),
                                                (i[0][0], i[0][1]), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                                                (255, 255, 255), 1, cv2.LINE_AA)

                                    cv2.line(self.frame, (i[0][0] - 10, i[0][1]), (i[0][0] + 10, i[0][1]), (255, 0, 255), 1)
                                    cv2.line(self.frame, (i[0][0], i[0][1] - 10), (i[0][0], i[0][1] + 10), (255, 0, 255), 1)

                            if longest_coords:
                                cv2.line(self.frame, longest_coords[0], longest_coords[1], (0, 255, 255), 2)

                                if (longest_coords[0][1] - longest_coords[1][1]) / (
                                        longest_coords[0][0] - longest_coords[1][0]) >= 0:

                                    cv2.putText(self.frame, 'RIGHT',
                                                longest_coords[0], cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                                                (255, 255, 255), 1, cv2.LINE_AA)

                                    right.append(points)

                                else:

                                    cv2.putText(self.frame, 'LEFT',
                                                longest_coords[0], cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                                                (255, 255, 255), 1, cv2.LINE_AA)

                                    left.append(points)

            left.sort()
            right.sort()

            for l in range(len(left)):

                for r in range(len(right)):

                    left_piece = left[l][:]
                    right_piece = right[r][:]

                    boundary_h = max(left_piece[5], right_piece[5])
                    boundary_w = boundary_h * self.TARGET_RATIO

                    print(boundary_w, boundary_h)

                    if abs(left[l][0] - right[r][0]) <= boundary_w and abs(left[l][1] - right[r][1]) <= boundary_h and left[l][0] < right[r][0]:
                        del right[r]

                        break

                else:
                    continue

                print(left_piece, right_piece)

                if not self.headless:

                    cv2.circle(self.frame, (left_piece[0], left_piece[1]), 10, (255, 0, 0), 1)
                    cv2.circle(self.frame, (right_piece[0], right_piece[1]), 10, (255, 0, 0), 1)

                    cv2.putText(self.frame, 'LEFTH: %i' % (left_piece[5]),
                                (left_piece[2], 100), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                                (255, 255, 255), 1, cv2.LINE_AA)

                    cv2.rectangle(self.frame, (left_piece[2], left_piece[3]),
                                  (left_piece[2] + left_piece[4], left_piece[3] + left_piece[5]), (255, 0, 0), 1)

                    cv2.putText(self.frame, 'RIGHTH: %i'% (right_piece[5]),
                                (right_piece[2], 100), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                                (255, 255, 255), 1, cv2.LINE_AA)

                    cv2.rectangle(self.frame, (right_piece[2], right_piece[3]),
                                  (right_piece[2] + right_piece[4], right_piece[3] + right_piece[5]), (0, 255, 0), 1)

                    cv2.rectangle(self.frame, (left_piece[2], min(left_piece[3], right_piece[3])), (
                    right_piece[2] + right_piece[4], max(left_piece[3] + left_piece[5], right_piece[3] + right_piece[5])),
                                  (255, 255, 0), 1)

                    rect = (left_piece[2], min(left_piece[3], right_piece[3]), right_piece[2] + right_piece[4] - left_piece[2], max(left_piece[3] + left_piece[5], right_piece[3] + right_piece[5]) - min(left_piece[3], right_piece[3]))

                    dist_to_centre = abs(rect[0] + rect[2] // 2 - self.WIDTH // 2)

                    cv2.line(self.frame, (rect[0] + rect[2] // 2, 0), (rect[0] + rect[2] // 2, self.HEIGHT), (0, 255, 0), 1)

                    cv2.putText(self.frame, 'S: %i W: %i'% (rect[1] * self.TARGET_RATIO, rect[0]),
                                (rect[0] + rect[2] // 2, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                                (255, 255, 255), 1, cv2.LINE_AA)

                    if dist_to_centre < min_deviation:
                        min_deviation = dist_to_centre

                    # dim 14.5 x 6


            if min_deviation != 999999:

                # angle = FOV * (mx / WIDTH) - FOV / 2

                #angle = math.degrees(math.atan((2 * (mx - WIDTH / 2) * math.tan(math.radians(FOV // 2))) / WIDTH))

                angle = 0

                if not self.headless:
                    if angle < 0:
                        rotate_msg = 'rotate left! <='
                    elif angle > 0:
                        rotate_msg = 'rotate right! =>'
                    else:
                        rotate_msg = 'don\'t rotate! </>'

                    if min_deviation < 0:
                        deviation_msg = 'move left! <='
                    elif min_deviation > 0:
                        deviation_msg = 'move right! =>'
                    else:
                        deviation_msg = 'don\'t move! </>'

                    #cv2.line(self.frame, (mx - 10, my), (mx + 10, my), (0, 0, 255), 1)
                    #cv2.line(self.frame, (mx, my - 10), (mx, my + 10), (0, 0, 255), 1)

                    cv2.putText(self.frame,
                                'Deviation: %i | Angle to center: %2.2f degrees | (This means you %s and %s)' % (
                                    min_deviation, angle, rotate_msg, deviation_msg),
                                (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1, cv2.LINE_AA)

                self.table.putNumber('heading', angle)
                self.table.putNumber('deviation', min_deviation)
                self.table.putNumber('lastUpdated', time.time())

                self.table.putNumber('locked', 1)

            else:

                self.table.putNumber('heading', 0)
                self.table.putNumber('deviation', 0)
                self.table.putNumber('locked', 0)

                self.table.putNumber('lastUpdated', time.time())

                if not self.headless:
                    cv2.putText(self.frame, 'Target not found', (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1,
                                cv2.LINE_AA)

            if not self.headless:
                cv2.line(self.frame, (self.WIDTH // 2, 0), (self.WIDTH // 2, self.HEIGHT), (0, 0, 255), 1)

                self.res = cv2.bitwise_and(self.frame, self.frame, mask=self.mask)

if __name__ == '__main__':

    if len(sys.argv) == 2 and sys.argv[-1] == 'display':
        HEADLESS = False
    else:
        HEADLESS = True

    camID = 2

    at = AutoTarget(HEADLESS, camID)

    print('Hai')

    while True:
        cv2.imshow('self.frame', at.frame)
        cv2.imshow('image', at.mask)
        cv2.imshow('res', at.res)

        k = cv2.waitKey(5) & 0xFF
        if k == 27:
            break
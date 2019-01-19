import cv2
import numpy as np
import traceback
import threading
import time
import sys
import os
import math

class AutoTarget:
    def __init__(self, headless, camID):
        self.cap = cv2.VideoCapture(camID)
        self.headless = headless
        self.FOV = 70

        self.W = 1024
        self.H = 615

        self.Y_DEVIATION = 100
        self.X_DEVIATION = 200

        self.frame = np.ones((self.H, self.W, 3), dtype=np.uint8)
        self.mask = np.ones((self.H, self.W, 3), dtype=np.uint8)
        self.res = np.ones((self.H, self.W, 3), dtype=np.uint8)

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
        os.system('v4l2-ctl -d %i -c saturation=100' % camID)
        os.system('v4l2-ctl -d %i -c exposure_auto=1' % camID)
        os.system('v4l2-ctl -d %i -c exposure_absolute=0' % camID)

        print('Cam ID %i succeeded' % camID)

        self.cap.set(3, self.W)
        self.cap.set(4, self.H)

        self.HEIGHT, self.WIDTH, _ = self.cap.read()[1].shape

        self.upper_thresh = np.array([255, 255, 255])
        self.lower_thresh = np.array([58, 164, 50])

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
            points = []

            left = []
            right = []
            group = []

            for c in cnts:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.02 * peri, True)
                x, y, w, h = cv2.boundingRect(approx)

                approx = list(approx)

                approx.append(approx[0])

                longest = -1
                longest_coords = []

                if h >= 20 and w >= 20:
                    rect = (x, y, w, h)
                    rects.append(rect)

                    if abs(len(approx) - 4) <= 2:
                        points = [x + w // 2, y + h // 2, x, y, w, h, len(approx)]

                        if not self.headless:

                            prev = ()

                            count = 0

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

                    if abs(left[l][0] - right[r][0]) <= self.X_DEVIATION and abs(left[l][1] - right[r][1]) <= self.Y_DEVIATION and \
                            left[l][0] < right[r][0]:
                        left_piece = left[l][:]
                        right_piece = right[r][:]

                        del right[r]

                        break

                else:
                    continue

                if not self.headless:

                    cv2.circle(self.frame, (left_piece[0], left_piece[1]), 10, (255, 0, 0), 1)
                    cv2.circle(self.frame, (right_piece[0], right_piece[1]), 10, (255, 0, 0), 1)

                    cv2.rectangle(self.frame, (left_piece[2], left_piece[3]),
                                  (left_piece[2] + left_piece[4], left_piece[3] + left_piece[5]), (255, 0, 0), 1)
                    cv2.rectangle(self.frame, (right_piece[2], right_piece[3]),
                                  (right_piece[2] + right_piece[4], right_piece[3] + right_piece[5]), (0, 255, 0), 1)

                    cv2.rectangle(self.frame, (left_piece[2], min(left_piece[3], right_piece[3])), (
                    right_piece[2] + right_piece[4], max(left_piece[3] + left_piece[5], right_piece[3] + right_piece[5])),
                                  (255, 255, 0), 1)


            """
            if points and 10 > points[4] > 4:
                mx = points[0]
                my = points[1]

                # angle = FOV * (mx / WIDTH) - FOV / 2

                angle = math.degrees(math.atan((2 * (mx - WIDTH / 2) * math.tan(math.radians(FOV // 2))) / WIDTH))

                if not self.headless:
                    if angle < 0:
                        move = 'move left! <='
                    elif angle > 0:
                        move = 'move right! =>'
                    else:
                        move = 'don\'t move! </>'

                    cv2.line(self.frame, (mx - 10, my), (mx + 10, my), (0, 0, 255), 1)
                    cv2.line(self.frame, (mx, my - 10), (mx, my + 10), (0, 0, 255), 1)

                    cv2.putText(self.frame,
                                'Deviation: %i | Angle to center: %2.2f degrees | (This means you %s)' % (
                                    points[4] - 8, angle, move),
                                (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1, cv2.LINE_AA)

                #table.putNumber('heading', angle)
                #table.putNumber('deviation', points[4] - 8)
                #table.putNumber('lastUpdated', time.time() + offset)

                #if not target_locked:
                #    target_locked = True
                #    table.putNumber('locked', 1)

                    # locked()
            else:

                if target_locked:
                    target_locked = False

                    table.putNumber('heading', 9000)
                    table.putNumber('locked', 0)

                    # unlocked()

                table.putNumber('lastUpdated', time.time() + offset)

                if not self.headless:
                    cv2.putText(self.frame, 'Target not found', (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1,
                                cv2.LINE_AA)
            """

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
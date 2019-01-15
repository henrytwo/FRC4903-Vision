import cv2
import numpy as np
import multiprocessing
import traceback
import logging
import time
import sys
import os
import math
from networktables import NetworkTables

from GPIOInterface import *

if len(sys.argv) == 2 and sys.argv[-1] == 'display':
    HEADLESS = False
else:
    HEADLESS = True

camID = 2

if __name__ == '__main__':

    try:
        # initializing()

        # Try camera ID
        cap = cv2.VideoCapture(camID)

        os.system('v4l2-ctl -d %i -c white_balance_temperature_auto=0' % camID)
        os.system('v4l2-ctl -d %i -c saturation=100' % camID)
        os.system('v4l2-ctl -d %i -c exposure_auto=1' % camID)
        os.system('v4l2-ctl -d %i -c exposure_absolute=0' % camID)

        print('Cam ID %i succeeded' % camID)

        # Set frame size
        #cap.set(3, 1024)
        #cap.set(4, 615)

        offset = 0

        # Set upper and lower boundary
        upper_thresh = np.array([255, 255, 255])
        lower_thresh = np.array([58, 164, 50])

        # FOV of the camera
        FOV = 70

        # Size of the image
        HEIGHT, WIDTH, _ = cap.read()[1].shape

        Y_DEVIATION = 100
        X_DEVIATION = 200

        halted = True
        target_locked = False

        prev_time = 0

        # DO this forever
        while True:

            prev_time = time.time()

            # Get frame
            #_, frame = cap.read()
            frame = cv2.imread('manydark.png', 1)

            # Convert to HSV
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Create mask
            mask = cv2.inRange(hsv, lower_thresh, upper_thresh)

            im2, cnts, hierarchy = cv2.findContours(mask.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

            rects = []
            points = []
            #max_area = -1

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
                    # if height is enough
                    # create rectangle for bounding
                    rect = (x, y, w, h)
                    rects.append(rect)

                    if abs(len(approx) - 4) <= 2: #(not points or (abs(len(approx) - 4) < abs(points[4] - 4))) and w * h > max_area:
                        points = [x + w // 2, y + h // 2, x, y, w, h, len(approx)]
                        #max_area = w * h

                        if not HEADLESS:
                            #cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 0), 1)

                            prev = ()

                            count = 0

                            for i in approx:
                                if prev:

                                    if math.hypot(i[0][0] - prev[0], i[0][1] - prev[1]) > longest:
                                        longest = math.hypot(i[0][0] - prev[0], i[0][1] - prev[1])
                                        longest_coords = [prev, (i[0][0], i[0][1])]

                                    cv2.line(frame, prev, (i[0][0], i[0][1]), (0, 0, 255), 1)

                                prev = (i[0][0], i[0][1])

                                count += 1

                                cv2.putText(frame,
                                            '%i' % (count),
                                            (i[0][0], i[0][1]), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                                            (255, 255, 255), 1, cv2.LINE_AA)

                                cv2.line(frame, (i[0][0] - 10, i[0][1]), (i[0][0] + 10, i[0][1]), (255, 0, 255), 1)
                                cv2.line(frame, (i[0][0], i[0][1] - 10), (i[0][0], i[0][1] + 10), (255, 0, 255), 1)

                            if longest_coords:
                                cv2.line(frame, longest_coords[0], longest_coords[1], (0, 255, 255), 2)

                                if (longest_coords[0][1] - longest_coords[1][1]) / (longest_coords[0][0] - longest_coords[1][0]) >= 0:

                                    cv2.putText(frame, 'RIGHT',
                                                longest_coords[0], cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                                                (255, 255, 255), 1, cv2.LINE_AA)

                                    right.append(points)

                                else:

                                    cv2.putText(frame, 'LEFT',
                                                longest_coords[0], cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                                                (255, 255, 255), 1, cv2.LINE_AA)

                                    left.append(points)

            left.sort()
            right.sort()

            for l in range(len(left)):

                for r in range(len(right)):

                    if abs(left[l][0] - right[r][0]) <= X_DEVIATION and abs(left[l][1] - right[r][1]) <= Y_DEVIATION and left[l][0] < right[r][0]:

                        left_piece = left[l][:]
                        right_piece = right[r][:]

                        del right[r]

                        break

                else:
                    continue

                cv2.circle(frame, (left_piece[0], left_piece[1]), 10, (255, 0, 0), 1)
                cv2.circle(frame, (right_piece[0], right_piece[1]), 10, (255, 0, 0), 1)

                cv2.rectangle(frame, (left_piece[2], left_piece[3]), (left_piece[2] + left_piece[4], left_piece[3] + left_piece[5]), (255, 0, 0), 1)
                cv2.rectangle(frame, (right_piece[2], right_piece[3]), (right_piece[2] + right_piece[4], right_piece[3] + right_piece[5]), (0, 255, 0), 1)

                cv2.rectangle(frame, (left_piece[2], min(left_piece[3], right_piece[3])), (right_piece[2] + right_piece[4], max(left_piece[3] + left_piece[5], right_piece[3] + right_piece[5])), (255, 255, 0), 1)

            #print('left', left, '\nright', right)

            """
            if points and 10 > points[4] > 4:
                mx = points[0]
                my = points[1]

                # angle = FOV * (mx / WIDTH) - FOV / 2

                angle = math.degrees(math.atan((2 * (mx - WIDTH / 2) * math.tan(math.radians(FOV // 2))) / WIDTH))

                if not HEADLESS:
                    if angle < 0:
                        move = 'move left! <='
                    elif angle > 0:
                        move = 'move right! =>'
                    else:
                        move = 'don\'t move! </>'

                    cv2.line(frame, (mx - 10, my), (mx + 10, my), (0, 0, 255), 1)
                    cv2.line(frame, (mx, my - 10), (mx, my + 10), (0, 0, 255), 1)

                    cv2.putText(frame,
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

                if not HEADLESS:
                    cv2.putText(frame, 'Target not found', (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1,
                                cv2.LINE_AA)
            """

            if not HEADLESS:
                cv2.line(frame, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), (0, 0, 255), 1)

                res = cv2.bitwise_and(frame, frame, mask=mask)

                cv2.imshow('frame', frame)
                cv2.imshow('image', mask)
                cv2.imshow('res', res)

            k = cv2.waitKey(5) & 0xFF
            if k == 27:
                break

            #print(time.time() - prev_time)

    except:
        traceback.print_exc()
        # error()

        try:
            cv2.destroyAllWindows()
            cap.release()
        except:
            pass

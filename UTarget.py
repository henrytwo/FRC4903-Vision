import cv2
import numpy as np
import multiprocessing
import traceback
import logging
import time
import sys
from networktables import NetworkTables

if len(sys.argv) == 2 and sys.argv[-1] == 'display':
    HEADLESS = False
else:
    HEADLESS = True



def locked():
    print('Locked on target')

def unlocked():
    print('Target not locked')

def disabled():
    print('Disabled')

def error():
    print('Something went wrong')

def initializing():
    print('Initializing')

def nt_read():
    pass

def nt_write():
    pass

def changeListener(key, value, isNew):

    #print(key, value, isNew)

    if key == '/Vision/enabled':
        halt_queue.put('GO' if value else 'STOP')

    elif key == '/Vision/time':
        offset = time.time() - value
        print('TIME OFFSET', offset)
        table.putNumber('offset', offset)

    #halt_queue.put("GO")

if __name__ == '__main__':

    try:
        initializing()
        #10.88.195.46
        NetworkTables.initialize(server='localhost')
        NetworkTables.addEntryListener(changeListener)
        table = NetworkTables.getTable("Vision")

        table.putNumber('getTime', 1)

        logging.basicConfig(level=logging.DEBUG)

        offset = 0

        halt_queue = multiprocessing.Queue()

        # Selecting camera
        cap = cv2.VideoCapture(0)

        # Set frame size
        cap.set(3, 1024)
        cap.set(4, 615)

        # FOV of the camera
        FOV = 125.718

        # Makes the window
        #cv2.namedWindow('image')

        # Size of the image
        HEIGHT, WIDTH, _ = cap.read()[1].shape

        halted = True
        target_locked = False

        # DO this forever
        while True:

            if halted:
                disabled()

                h = halt_queue.get()  # STOP HERE

                if h == 'GO':
                    halted = False

            elif not halt_queue.empty():
                if halt_queue.get() == 'STOP':
                    halted = True

            # Get frame
            _, frame = cap.read()

            # Convert to HSV
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Set upper and lower boundary
            upper_thresh = np.array([255, 255, 255])
            lower_thresh = np.array([0, 0, 126])

            # Create mask
            mask = cv2.inRange(hsv, lower_thresh, upper_thresh)
            res = cv2.bitwise_and(frame, frame, mask=mask)

            im2, cnts, hierarchy = cv2.findContours(mask.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

            cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:2]

            rects = []
            points = []

            for c in cnts:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.02 * peri, True)
                x, y, w, h = cv2.boundingRect(approx)

                if h >= 10 and w >= 10:
                    # if height is enough
                    # create rectangle for bounding
                    rect = (x, y, w, h)
                    rects.append(rect)

                    # w * h > points[2] * points[3] and

                    if not points or (abs(len(approx) - 8) < abs(points[4] - 8)):
                        points = [x + w // 2, y + h // 2, w, h, len(approx)]

                        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 0), 1)

                        prev = ()

                        for i in approx:
                            # print(i[0][0])

                            if prev:
                                cv2.line(frame, prev, (i[0][0], i[0][1]), (255, 255, 0), 1)

                            prev = (i[0][0], i[0][1])

                            cv2.line(frame, (i[0][0] - 10, i[0][1]), (i[0][0] + 10, i[0][1]), (255, 0, 255), 1)
                            cv2.line(frame, (i[0][0], i[0][1] - 10), (i[0][0], i[0][1] + 10), (255, 0, 255), 1)


                    else:
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)

                    cv2.putText(frame, 'I think this has %i sides' % len(approx), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                                (0, 255, 0), 1, cv2.LINE_AA)

            if points and points[4] > 4:
                mx = points[0]
                my = points[1]

                angle = FOV * (mx / WIDTH) - FOV / 2

                if angle > 0:
                    move = 'move left! <='
                elif angle < 0:
                    move = 'move right! =>'
                else:
                    move = 'don\'t move! </>'

                # cv2.circle(frame, (mx, my), 20, (0, 0, 255), 1)

                cv2.line(frame, (mx - 10, my), (mx + 10, my), (0, 0, 255), 1)
                cv2.line(frame, (mx, my - 10), (mx, my + 10), (0, 0, 255), 1)

                cv2.putText(frame,
                            'Deviation: %i | Angle to center: %2.2f degrees | (This means you %s)' % (
                            points[4] - 8, angle, move),
                            (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1, cv2.LINE_AA)
                #print(angle, mx - WIDTH // 2)

                table.putNumber('heading', angle)
                table.putNumber('deviation', points[4] - 8)
                table.putNumber('lastUpdated', time.time() + offset)

                if not target_locked:
                    target_locked = True
                    table.putNumber('locked', 1)
                    locked()
            else:

                if target_locked:
                    target_locked = False

                    table.putNumber('heading', 0)
                    table.putNumber('locked', 0)
                    unlocked()

                table.putNumber('lastUpdated', time.time() + offset)

                cv2.putText(frame, 'Target not found', (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1,
                            cv2.LINE_AA)

            cv2.line(frame, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), (0, 0, 255), 1)

            res = cv2.bitwise_and(frame, frame, mask=mask)

            if not HEADLESS:
                cv2.imshow('frame', frame)
                cv2.imshow('image', mask)
                cv2.imshow('res', res)

            k = cv2.waitKey(5) & 0xFF
            if k == 27:
                break

    except:
        traceback.print_exc()
        error()

        cv2.destroyAllWindows()
        cap.release()
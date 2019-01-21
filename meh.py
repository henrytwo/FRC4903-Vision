import cv2
import numpy as np
import math
cap = cv2.VideoCapture(2)

FOV = 57.62158749
#asd

def nothing(x):
    pass


cv2.namedWindow('image')

HEIGHT, WIDTH, IDK = cap.read()[1].shape

while (1):
    _, frame = cap.read()
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    upper_red = np.array([138, 125, 89])
    lower_red = np.array([52, 32, 51])


    mask = cv2.inRange(hsv, lower_red, upper_red)

    im2, cnts, hierarchy = cv2.findContours(mask.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:2]

    rects = []
    points = []

    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        x, y, w, h = cv2.boundingRect(approx)

        approx = list(approx)

        approx.append(approx[0])

        longest = -1
        longest_coords = []

        if h >= 30 and w >= 30:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)

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

    res = cv2.bitwise_and(frame, frame, mask=mask)

    cv2.imshow('frame', frame)
    cv2.imshow('image', mask)
    cv2.imshow('res', res)

    k = cv2.waitKey(5) & 0xFF
    if k == 27:
        break

cv2.destroyAllWindows()
cap.release()
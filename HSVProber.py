import cv2
import numpy as np

cap = cv2.VideoCapture(4)

FOV = 57.62158749


def nothing(x):
    pass


cap.set(cv2.CAP_PROP_FRAME_WIDTH, 683 * 0.75)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 384 * 0.75)


cv2.namedWindow('image')
cv2.createTrackbar('HU', 'image', 0, 255, nothing)
cv2.createTrackbar('SU', 'image', 0, 255, nothing)
cv2.createTrackbar('VU', 'image', 0, 255, nothing)

cv2.createTrackbar('HL', 'image', 0, 255, nothing)
cv2.createTrackbar('SL', 'image', 0, 255, nothing)
cv2.createTrackbar('VL', 'image', 0, 255, nothing)

HEIGHT, WIDTH, IDK = cap.read()[1].shape

while (1):
    _, frame = cap.read()
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # [ 29 117 153]

    # upper_red = np.array([209,196,255])
    # lower_red = np.array([0, 0, 33])

    # [122.54347826086956, 43.93478260869565, 80.30434782608695]

    lower_red = np.array(
        [cv2.getTrackbarPos('HL', 'image'), cv2.getTrackbarPos('SL', 'image'), cv2.getTrackbarPos('VL', 'image')])
    upper_red = np.array(
        [cv2.getTrackbarPos('HU', 'image'), cv2.getTrackbarPos('SU', 'image'), cv2.getTrackbarPos('VU', 'image')])

    mask = cv2.inRange(hsv, lower_red, upper_red)

    im2, cnts, hierarchy = cv2.findContours(mask.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:2]

    rects = []
    points = []

    res = cv2.bitwise_and(frame, frame, mask=mask)

    cv2.imshow('frame', frame)
    cv2.imshow('image', mask)
    cv2.imshow('res', res)

    k = cv2.waitKey(5) & 0xFF
    if k == 27:
        break

cv2.destroyAllWindows()
cap.release()
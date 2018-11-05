import cv2
import numpy as np

# Selecting camera
cap = cv2.VideoCapture(2)

# FOV of the camera
FOV = 57.62158749


# Stuff
def nothing(x):
    pass


# Makes the window
cv2.namedWindow('image')
# cv2.createTrackbar('HU','image',0,255,nothing)
# cv2.createTrackbar('SU','image',0,255,nothing)
# cv2.createTrackbar('VU','image',0,255,nothing)

# cv2.createTrackbar('HL','image',0,255,nothing)
# cv2.createTrackbar('SL','image',0,255,nothing)
# cv2.createTrackbar('VL','image',0,255,nothing)

# Size of the image
HEIGHT, WIDTH, IDK = cap.read()[1].shape

# DO this forever
while (1):

    # Get frame
    _, frame = cap.read()

    # Convert to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Set upper and lower boundary
    upper_red = np.array([209, 196, 255])
    lower_red = np.array([0, 0, 33])

    # [122.54347826086956, 43.93478260869565, 80.30434782608695]

    # lower_red = np.array([cv2.getTrackbarPos('HL','image'), cv2.getTrackbarPos('SL','image'), cv2.getTrackbarPos('VL','image')])
    # upper_red = np.array([cv2.getTrackbarPos('HU','image'), cv2.getTrackbarPos('SU','image'), cv2.getTrackbarPos('VU','image')])

    # Create mask
    mask = cv2.inRange(hsv, lower_red, upper_red)
    # res = cv2.bitwise_and(frame,frame, mask= mask)

    im2, cnts, hierarchy = cv2.findContours(mask.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:2]

    # print(cnts)

    rects = []
    points = []

    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        x, y, w, h = cv2.boundingRect(approx)

        if h >= 30 and w >= 30:
            # print(FOV * (x - W // 2) / W, y - H // 2)

            # if height is enough
            # create rectangle for bounding
            rect = (x, y, w, h)
            rects.append(rect)

            points.append((x + w // 2, y + h // 2))

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1);

    if len(points) == 2:
        mx = (points[0][0] + points[1][0]) // 2
        my = (points[0][1] + points[1][1]) // 2

        # cv2.circle(frame, points[0], 20, (0, 0, 255), 1)
        # cv2.circle(frame, points[1], 20, (0, 0, 255), 1)

        angle = FOV * (mx / WIDTH) - FOV // 2

        if int(angle) > 0:
            move = 'move right!'
        elif int(angle) < 0:
            move = 'move left!'
        else:
            move = 'don\'t move!'

        cv2.circle(frame, (mx, my), 20, (0, 0, 255), 1)
        cv2.putText(frame, 'TARGET AQUIREDDD!!!!!! Angle to center: %i degrees | (This means you %s)' % (angle, move),
                    (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1, cv2.LINE_AA)
        print(angle)
    else:
        cv2.putText(frame, 'Target not found', (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)

    """
    for r in range(len(rects)):

        for runner 
    """

    res = cv2.bitwise_and(frame, frame, mask=mask)

    cv2.imshow('frame', frame)
    cv2.imshow('image', mask)
    cv2.imshow('res', res)

    k = cv2.waitKey(5) & 0xFF
    if k == 27:
        break

cv2.destroyAllWindows()
cap.release()

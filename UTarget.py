import cv2
import numpy as np

# Selecting camera
cap = cv2.VideoCapture(2)

# Set frame size
cap.set(3, 1024)
cap.set(4, 615)

# FOV of the camera
FOV = 125.718

# Makes the window
cv2.namedWindow('image')

# Size of the image
HEIGHT, WIDTH, IDK = cap.read()[1].shape

# DO this forever
while True:

    # Get frame
    _, frame = cap.read()

    # Convert to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Set upper and lower boundary
    upper_red = np.array([255, 255, 255])
    lower_red = np.array([0, 0, 126])

    # Create mask
    mask = cv2.inRange(hsv, lower_red, upper_red)
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

            #w * h > points[2] * points[3] and
            
            if not points or (abs(len(approx) - 8) < abs(points[4] - 8)):
                points = [x + w // 2, y + h // 2, w, h, len(approx)]

                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 0), 1)
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

        #cv2.circle(frame, (mx, my), 20, (0, 0, 255), 1)

        cv2.line(frame, (mx - 10, my), (mx + 10, my), (0, 0, 255), 1)
        cv2.line(frame,  (mx, my - 10), (mx, my + 10), (0, 0, 255), 1)

        cv2.putText(frame,
                    'Deviation: %i | Angle to center: %2.2f degrees | (This means you %s)' % (points[4] - 8, angle, move),
                    (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1, cv2.LINE_AA)
        print(angle, mx - WIDTH // 2)
    else:
        cv2.putText(frame, 'Target not found', (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1, cv2.LINE_AA)

    cv2.line(frame, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), (0, 0, 255), 1)

    res = cv2.bitwise_and(frame, frame, mask=mask)

    cv2.imshow('frame', frame)
    cv2.imshow('image', mask)
    cv2.imshow('res', res)

    k = cv2.waitKey(5) & 0xFF
    if k == 27:
        break

cv2.destroyAllWindows()
cap.release()
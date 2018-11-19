v4l2-ctl -d /dev/video0 -c brightness=30
v4l2-ctl -d /dev/video0 -c saturation=0
v4l2-ctl -d /dev/video0 -c exposure_auto=1
v4l2-ctl -d /dev/video0 -c exposure_absolute=0
echo "Initialized."
python3 UTarget.py

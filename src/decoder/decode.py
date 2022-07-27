import rosbag
import pandas as pd
import cv2
from cv_bridge import CvBridge, CvBridgeError
import os

bag_name = '2022-07-27-18-06-34'
b = rosbag.Bag(f'{bag_name}.bag')

count = 0
path = f"{bag_name}/images/"

if not os.path.exists(path):
     os.makedirs(path)
     print('does not exist')
for topic, msg, t in b.read_messages(topics=['racecar/camera/zed/rgb/image_rect_color']):
    try:
        cv_image=CvBridge().imgmsg_to_cv2(msg,"bgr8")
        cv2.imwrite(f'{path}/image{count}.jpg',cv_image)
        count += 1
    except CvBridgeError as e:
        print(e)

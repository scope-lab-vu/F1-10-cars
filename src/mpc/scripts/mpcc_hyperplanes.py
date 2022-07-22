#!/usr/bin/env python

import rospy
from sensor_msgs.msg import Image, LaserScan
from ackermann_msgs.msg import AckermannDriveStamped
from nav_msgs.msg import Odometry
from race.msg import reach_tube
import sys
import os

import time


import math
import numpy as np
import scipy as sp


import pdb
import sys
sys.path.append('../../')
import do_mpc
from do_mpc.tools.timer import Timer
import copy 


from template_model import template_model
#from template_model_black_box import template_model
#from template_model_bicycle import template_model
from template_mpc import template_mpc
# from template_mpc_black_box import template_mpc
#from computing_hyperplanes_final import find_constraints


from constants import LEFT_DIVERGENCE_INDEX, RIGHT_DIVERGENCE_INDEX
from constants import FTG_IGNORE_RANGE, SAFETY_RADIUS, POSITION_PREDICTION_TIME
from constants import LIDAR_MINIMUM_ANGLE, LIDAR_ANGLE_INCREMENT, LIDAR_MAX_INDEX
from point import LidarPoint, CartesianPoint
from visualization_msgs.msg import Marker
from visualization_msgs.msg import MarkerArray
from geometry_msgs.msg import Point
#need to subscribe to the steering message and angle message
from message_filters import ApproximateTimeSynchronizer, Subscriber
import tf
import rospkg 
import csv


class MPCC: 

    # Constructor
    def __init__(self,waypoint_file,obstacle_file,racecar_name="racecar2"):
        self.log_hypers = False
        self.use_map  = False
        self.display_in_rviz = False
        self.use_pure_pursuit = True

        self.tar_x = 0 
        self.tar_y = 0
        self.tar_theta = 0
        self.x_min = 100
        self.x_max = -100
        self.y_min = 100
        self.y_max = -100
        self.speed_min = 0 
        self.speed_max = 1.3

        self.a0 = 1
        self.b0 = 1
        self.a1 = 1
        self.b1 = 1
        self.c1 = 1
        self.c2 = 1

        self.count = 0
        # mpc horizon
        # self.horizon = 5 so far the most successful horizon
        # self.horizon = 10 is too much

        # The horizon is probably the most important thing
        self.horizon = 4
        
        # set up the model used for the mpc controller
        self.model =  template_model()

        # set up the mpc controller
        self.mpc = template_mpc(self.model, self.horizon, -20, -20, 20, 20)  

        self.iter_time = rospy.Time.now()

        # set up the time varying function for mpc
        self.mpc.set_tvp_fun(self.change_target_position_template)
        self.mpc.setup()

        self.left_points = []
        self.right_points = []

        self.read_waypoints(waypoint_file,obstacle_file)
        self.vis_pub = rospy.Publisher(racecar_name+'/hyper_planes', MarkerArray,queue_size=1)
        self.vis_pub3 = rospy.Publisher('opponent/convex_hull', MarkerArray,queue_size=1)
        if(racecar_name=='racecar'):
            self.drive_publish = rospy.Publisher('/vesc/ackermann_cmd_mux/input/teleop', AckermannDriveStamped, queue_size=1)
        elif(racecar_name=="racecar2"):
            self.drive_publish = rospy.Publisher('/vesc2/ackermann_cmd_mux/input/teleop', AckermannDriveStamped, queue_size=1)
        else:
            self.drive_publish = rospy.Publisher('/vesc3/ackermann_cmd_mux/input/teleop', AckermannDriveStamped, queue_size=1)
        self.vis_pub2 = rospy.Publisher(racecar_name+"/wallpoint_classification", MarkerArray, queue_size=1)

        # instantiate the subscribers

        self.lidar_sub = Subscriber(racecar_name+'/scan', LaserScan)
        self.odom_sub  = Subscriber(racecar_name+'/odom', Odometry)
        self.reach_sub = Subscriber('racecar/reach_tube', reach_tube)
        self.reach_sub2 = Subscriber('racecar3/reach_tube', reach_tube)
        self.pp_sub = Subscriber(racecar_name+'/goal_point', MarkerArray)

      
        self.u0 = [0,0]

        #create the time synchronizer
        self.main_sub = ApproximateTimeSynchronizer([self.lidar_sub,self.odom_sub,self.reach_sub,self.reach_sub2,self.pp_sub], queue_size = 1, slop = 0.05,allow_headerless=True)
        
        #register the callback to the synchronizer
        self.main_sub.registerCallback(self.main_callback)


    # this function is for changing the target position without having to 
    # reframe the mpc problem
    def change_target_position_template(self, _):
        """
        Following the docs of do_mpc, an approach to populate the target position variables with values, at any given \
        point.
        """
        template = self.mpc.get_tvp_template()
        for k in range(self.horizon + 1):
            template["_tvp", k, "target_x"] = self.tar_x
            template["_tvp", k, "target_y"] = self.tar_y
            template["_tvp",k,"target_theta"] = self.tar_theta
            template["_tvp", k, "a0"] = self.a0
            template["_tvp", k, "b0"] = self.b0
            template["_tvp", k, "a1"] = self.a1
            template["_tvp", k, "b1"] = self.b1
            template["_tvp", k, "c1"] = self.c1
            template["_tvp", k, "c2"] = self.c2
            template["_tvp", k, "x_min"] = self.x_min
            template["_tvp", k, "x_max"] = self.x_max
            template["_tvp", k, "y_min"] = self.y_min
            template["_tvp", k, "y_max"] = self.y_max
            template["_tvp", k, "speed_min"] = self.speed_min
            template["_tvp", k, "speed_max"] = self.speed_max
            
            

        return template


    # convert lidar scans to cartesian point
    def lidar_to_cart(self,ranges, position_x, position_y, heading_angle, starting_index):

        points = []
        markerArray = MarkerArray()
        for index, lidar_range in enumerate(ranges):
            curr_index = starting_index + index
            # if(curr_index>180 and curr_index<900):
            #      continue
            angle=((starting_index + index)-540)/4.0
            rad=(angle*math.pi)/180
            laser_beam_angle = rad

            rotated_angle = laser_beam_angle + heading_angle

            # the 0.265 is the lidar's offset along the x-axis of the car
            # it's in the xacro file
            x_coordinate = (lidar_range) * math.cos(rotated_angle) + position_x + 0.265*math.cos(heading_angle)
            y_coordinate = (lidar_range) * math.sin(rotated_angle) + position_y + 0.265*math.sin(heading_angle)
            
            p3 = [x_coordinate,y_coordinate]
                        
            if(curr_index>540):
                self.left_points.append(p3)
            else:
                self.right_points.append(p3)

        


    # Import waypoints.csv into a list (path_points)
    def read_waypoints(self,waypoint_file,obstacle_file):

        # get an instance of RosPack with the default search paths
        rospack = rospkg.RosPack()

        #get the path for the waypoints
        package_path=rospack.get_path('pure_pursuit')
        filename=os.path.sep.join([package_path,'waypoints',waypoint_file])

        # list of xy pts 
        self.xy_points = self.read_points(filename)

        # eulers for 
        self.eulers  = []
        with open(filename) as f:
            self.eulers = [tuple(line)[2] for line in csv.reader(f)]
        self.eulers = np.asarray(self.eulers).astype('double')

        # get path to obstacle points
        package_path=rospack.get_path('race')
        filename=os.path.sep.join([package_path,'maps',obstacle_file])

        # list of wall_points
        self.wall_points = self.read_points(filename)

        

    def read_points(self,filename):

        with open(filename) as f:
            path_points = [tuple(line) for line in csv.reader(f)]

        # Turn path_points into a list of floats to eliminate the need for casts in the code below.
        path_points_x   = np.asarray([float(point[0]) for point in path_points])
        path_points_y   = np.asarray([float(point[1]) for point in path_points])

        # list of xy pts 
        xy_points = np.hstack((path_points_x.reshape((-1,1)),path_points_y.reshape((-1,1)))).astype('double')
        return xy_points


    """
    Helper Functions
    """

    def is_left(self,p1,p2,p3):
        return ((p2[0] - p1[0])*(p3[1] - p1[1]) - (p2[1] - p1[1])*(p3[0] - p1[0])) > 0

    """
    Main Callback 
    """

    # The main callback functions of mpc are called within this callback
    def main_callback(self,lidar_data,pose_msg,hypes_opp1,hypes_opp2,pp_point):
        
        orig_point = copy.deepcopy(pp_point)
        lidar_data = np.asarray(lidar_data.ranges)
        indices = np.where(lidar_data>10)[0]
        lidar_data[indices] = 10
        quaternion = np.array([pose_msg.pose.pose.orientation.x,
                            pose_msg.pose.pose.orientation.y,
                            pose_msg.pose.pose.orientation.z,
                            pose_msg.pose.pose.orientation.w])

        position = [pose_msg.pose.pose.position.x, pose_msg.pose.pose.position.y, pose_msg.pose.pose.position.z]

        euler = tf.transformations.euler_from_quaternion(quaternion)

        quaternion_z = pose_msg.pose.pose.orientation.z
        quaternion_w = pose_msg.pose.pose.orientation.w

        head_angle = euler[2]

        # linear velocity 
        velx = pose_msg.twist.twist.linear.x
        vely = pose_msg.twist.twist.linear.y
        velz = pose_msg.twist.twist.linear.z

        # magnitude of velocity 
        speed = np.asarray([velx,vely])
        speed = np.linalg.norm(speed)

        pos_x,pos_y = position[0],position[1]
        pos_1x, pos1_y = pos_x + math.cos(head_angle) * 1.0, pos_y + math.sin(head_angle)*1.0
        

        curr_pos= np.asarray([pos_x,pos_y]).reshape((1,2))
        dist_arr = np.linalg.norm(self.wall_points-curr_pos,axis=-1)

        ##finding those points which are less than 3m away 
        relevant_points = np.where((dist_arr < 10.0))[0]
        
        if(self.use_map):
            # finding the goal point which is within the goal points 
            pts = self.wall_points[relevant_points]

            if(len(pts)>0):
                p1 = (pos_x,pos_y)
                p2 = (pos_1x,pos1_y)
                for pt in pts:
                    p3 = (pt[0],pt[1])

                    if(self.is_left(p1,p2,p3)):
                        self.left_points.append(p3)
                    else:
                        self.right_points.append(p3)

            if(len(self.left_points)>0 and len(self.right_points)>0):

                self.left_points  = np.asarray(self.left_points).reshape((-1,2))
                self.right_points  = np.asarray(self.right_points).reshape((-1,2))

                

                curr_pos= np.asarray([pos_x,pos_y]).reshape((1,2))
                dist_arr = np.linalg.norm(self.left_points-curr_pos,axis=-1)
                dist_arr2 = np.linalg.norm(self.right_points-curr_pos,axis=-1)

                dist = 3.0 

                left_point = self.left_points[np.argmin(dist_arr)]
                lx, ly = left_point[0] + math.cos(head_angle) * dist, left_point[1] + math.sin(head_angle)*dist
                lx1, ly1 = left_point[0] + math.cos(head_angle) * (-dist), left_point[1] + math.sin(head_angle)*(-dist)
                line1 = [lx1,ly1,lx,ly]

                right_point = self.right_points[np.argmin(dist_arr2)]
                rx1, ry1 = right_point[0] + math.cos(head_angle) * (-dist), right_point[1] + math.sin(head_angle) * (-dist)
                rx, ry = right_point[0] + math.cos(head_angle) * dist, right_point[1] + math.sin(head_angle)*dist
                line2 = [rx1,ry1,rx,ry]
                self.left_points = []
                self.right_points = []
                
                self.visualize_lines([line1,line2])
        else:

            
            
            # convert each of the lidar points to cartesian
            self.lidar_to_cart(lidar_data,pos_x,pos_y,head_angle,0)
            
            # convert the points to numpy arrays to make distance computations easier
            self.left_points  = np.asarray(self.left_points).reshape((-1,2))
            self.right_points  = np.asarray(self.right_points).reshape((-1,2))
            
            # get the current position
            curr_pos= np.asarray([pos_x,pos_y]).reshape((1,2))
            
            # compute the distances to all the left points
            dist_arr = np.linalg.norm(self.left_points-curr_pos,axis=-1)

            # compute the distances to all the right points
            dist_arr2 = np.linalg.norm(self.right_points-curr_pos,axis=-1)

            # compute the distance to the closest waypoint
            dist_arr3 = np.linalg.norm(self.xy_points - curr_pos,axis=-1)

            center_angle = self.eulers[np.argmin(dist_arr3)]

            # half the distance of the lines
            dist = 3.0 

            left_point = self.left_points[np.argmin(dist_arr)]
            #left_point = self.left_points[-1]
            lx1, ly1 = left_point[0] + math.cos(center_angle) * dist, left_point[1] + math.sin(center_angle)*dist
            lx, ly = left_point[0] + math.cos(center_angle) * (-dist), left_point[1] + math.sin(center_angle)*(-dist)
            line1 = [lx,ly,lx1,ly1]
            
            
            right_point = self.right_points[np.argmin(dist_arr2)]
            #right_point = self.right_points[0]
            rx1, ry1 = right_point[0] + math.cos(center_angle) * (-dist), right_point[1] + math.sin(center_angle) * (-dist)
            rx, ry = right_point[0] + math.cos(center_angle) * dist, right_point[1] + math.sin(center_angle)*dist
            
            line2 = [rx,ry,rx1,ry1]

            self.visualize_lines([line1,line2])
            self.left_points = []
            self.right_points = []
            
        # creating inequalities 
        m  = (ly1 - ly) / (lx1 - lx)
        b = ly1 - (m*lx1)

        
        m1 = (ry1 - ry) / (rx1 - rx)
        b1 = ry1 - (m*rx1)

        # above the left line 
        print(m,m1,b,b1)
        print("cons1u:", 0>=((pos_x*m+b)-pos_y))
        # below the left line
        print("cons1b:", 0>=(pos_y)-(pos_x*m+b))
        # above the right line
        print("cons2u:", 0>=((pos_x*m1+b1)-pos_y))
        # below the right line 
        print("cons2b:", 0>=(pos_y)-(pos_x*m1+b1))

        if(0>=((pos_x*m+b)-pos_y)):
            self.c1 = 1
        else:
            self.c1 = -1

        if(0>=((pos_x*m1+b1)-pos_y)):
            self.c2 = 1
        else:
            self.c2 = -1

        point = orig_point.markers[0]

        tarx,tary = point.pose.position.x, point.pose.position.y

        tar_pos   = np.asarray([tarx,tary]).reshape((1,2))
        dist_arr3 = np.linalg.norm(self.xy_points - tar_pos,axis=-1)
        tar_theta = self.eulers[np.argmin(dist_arr3)]

        distance = (self.tar_x - pos_x) ** 2 + (self.tar_y - pos_y) ** 2
        
        if(True or self.count==0 or distance<1.9 or (rospy.Time.now()-self.iter_time).to_sec()>15):
            self.tar_x =  point.pose.position.x
            self.tar_y =  point.pose.position.y
            self.tar_theta  = tar_theta
            self.iter_time = rospy.Time.now()

        
        intervals = []
        # visualize the convex hull for sanity checking
        if(hypes_opp1.count>0):
            convex_hull = hypes_opp1.obstacle_list[hypes_opp1.count-1]
            intvl = [[convex_hull.x_min,convex_hull.x_max],
                    [convex_hull.y_min,convex_hull.y_max]]
            intervals.append(intvl)
            
            self.x_min,self.x_max,self.y_min,self.y_max = self.decide_bounds(pos_x,pos_y,intvl)
            print("x_min:",self.x_min,"x_max:",self.x_max,"y_min:",self.y_min,"y_max:",self.y_max)

        if(hypes_opp2.count>0):
            convex_hull = hypes_opp2.obstacle_list[hypes_opp2.count-1]
            intvl = [[convex_hull.x_min,convex_hull.x_max],
                    [convex_hull.y_min,convex_hull.y_max]]
            intervals.append(intvl)
            
            
            
        self.visualize_rectangles(intervals)


        # set the constants for the hyper-planes
        self.a0 = m
        self.b0 = b
        self.a1 = m1
        self.b1 = b1


                
        x0 = np.array([pos_x, pos_y, head_angle]).reshape(-1, 1)
        #x0 = np.array([pos_x, pos_y,speed,head_angle]).reshape(-1, 1)

        if(self.count==0):
            self.mpc.x0 = x0
            self.mpc.set_initial_guess()

        u0 = self.mpc.make_step(x0)
        self.u0 = u0
            

        drive_msg = AckermannDriveStamped()
        drive_msg.header.stamp = rospy.Time.now()
        drive_msg.drive.steering_angle = float(u0[1])
        
        speed = float(u0[0])
        drive_msg.drive.speed = speed
        self.drive_publish.publish(drive_msg)

        self.count+=1

        self.compute_bounding_box_for_racecar(pos_x,pos_y,head_angle)
        if(self.count>100):
            self.count = 1

    
    def compute_bounding_box_for_racecar(self,pos_x,pos_y,head_angle):
        rad=(45*math.pi)/180
        distance = 0.1939115
        rotated_angle = rad + head_angle
        x_1 = (distance) * math.cos(rotated_angle) + pos_x + 0.265*math.cos(head_angle)
        y_1 = (distance) * math.sin(rotated_angle) + pos_y + 0.265*math.sin(head_angle)

        rotated_angle = -rad + head_angle
        x_2 = (distance) * math.cos(rotated_angle) + pos_x + 0.265*math.cos(head_angle)
        y_2 = (distance) * math.sin(rotated_angle) + pos_y + 0.265*math.sin(head_angle)

        rad=(135*math.pi)/180
        rotated_angle = rad + head_angle
        x_3 = (distance) * math.cos(rotated_angle) + pos_x + 0.265*math.cos(head_angle)
        y_3 = (distance) * math.sin(rotated_angle) + pos_y + 0.265*math.sin(head_angle)

        rotated_angle = -rad + head_angle
        x_4 = (distance) * math.cos(rotated_angle) + pos_x + 0.265*math.cos(head_angle)
        y_4 = (distance) * math.sin(rotated_angle) + pos_y + 0.265*math.sin(head_angle)
        self.left_points = [[x_1,y_1],[x_2,y_2],[x_3,y_3],[x_4,y_4]]
        self.right_points = [[x_1,y_1],[x_2,y_2]]

        self.visualize_points()

        self.left_points = []
        self.right_points = []
    
    def visualize_points(self,frame='map'):
        # create a marker array
        markerArray = MarkerArray()
        for i in range(len(self.left_points)):
            pt = self.left_points[i]

            x = float(pt[0])
            y = float(pt[1])
            
            marker = Marker()
            marker.id = i 
            marker.header.frame_id = frame
            marker.type = marker.SPHERE
            marker.action = marker.ADD
            marker.scale.x = 0.2
            marker.scale.y = 0.2
            marker.scale.z = 0.2
            marker.color.a = 1.0
            marker.color.r = 1.0
            marker.color.g = 1.0
            marker.color.b = 0.0
            marker.pose.orientation.w = 1.0
            marker.pose.position.x = x
            marker.pose.position.y = y
            marker.pose.position.z = 0
            markerArray.markers.append(marker)

        for i in range(len(self.right_points)):
            pt = self.right_points[i]

            x = float(pt[0])
            y = float(pt[1])
            
            marker = Marker()
            marker.id = len(self.left_points)+i 
            marker.header.frame_id = frame
            marker.type = marker.SPHERE
            marker.action = marker.ADD
            marker.scale.x = 0.2
            marker.scale.y = 0.2
            marker.scale.z = 0.2
            marker.color.a = 1.0
            marker.color.r = 0.0
            marker.color.g = 1.0
            marker.color.b = 0.0
            marker.pose.orientation.w = 1.0
            marker.pose.position.x = x
            marker.pose.position.y = y
            marker.pose.position.z = 0
            markerArray.markers.append(marker)
        self.vis_pub2.publish(markerArray)

    def decide_bounds(self,x,y,convex_hull):

        x_min = convex_hull[0][0] 
        x_max = convex_hull[0][1]
        y_min = convex_hull[1][0]
        y_max = convex_hull[1][1]

        # case 1 
        if(x>=x_max and y<=y_min):
            return 100, x_max, y_min,-100
        # case2
        elif (x>=x_max and y>=y_max):
            return 100, x_max, 100, y_max
        # case 3
        elif(x<=x_min and y<=y_min):
            return x_min,-100,y_min,-100
        # case 4
        elif(x<=x_min and y>=y_max):
            return x_min,-100,100,y_max

        
        elif(x>=x_min and x<=x_max):
            if(y>=y_max):
                return 100,-100,100,y_max
            else:
                return 100,-100,y_min,-100

        elif(y>=y_min and y<=y_max):
            if(x>=x_max):
                return 100,x_max,100,-100
            else:
                return x_min,-100,100,-100

    def visualize_lines(self, lines):
        
        markerArray = MarkerArray()
        for i in range(2):
            line = lines[i]
            x1,y1,x2,y2 = line

            marker = Marker()
            marker.id = 10000 + i
            marker.header.frame_id = "map"
            marker.type = marker.LINE_STRIP
            marker.action = marker.ADD
            
            marker.color.a = 1.0
            marker.color.r = 1.0
            marker.color.g = 0.843
            marker.color.b = 0.0
            
            marker.scale.x = 0.1
            marker.scale.y = 0.1
            marker.scale.z = 0.05


            marker.pose.orientation.x = 0.0
            marker.pose.orientation.y = 0.0
            marker.pose.orientation.z = 0.0
            marker.pose.orientation.w = 1.0

            marker.points = []
            first_line_point = Point()
            first_line_point.x = x1
            first_line_point.y = y1
            first_line_point.z = 0.0
            marker.points.append(first_line_point)

            # second point
            second_line_point = Point()
            second_line_point.x = x2
            second_line_point.y = y2
            second_line_point.z = 0.0
            marker.points.append(second_line_point)
            
            markerArray.markers.append(marker)

        self.vis_pub.publish(markerArray)
        
    def visualize_rectangles(self,intervals):
        markerArray = MarkerArray()

        for i in range(len(intervals)):
            hull = intervals[i]

            marker = Marker()
            marker.id = i
            marker.header.frame_id = "map"
            marker.type = marker.CUBE
            marker.action = marker.ADD
            
            marker.pose.position.x = (hull[0][1]+hull[0][0])/2.0
            marker.pose.position.y = (hull[1][0]+hull[1][1])/2.0
            marker.pose.position.z = 0.0


            marker.pose.orientation.x = 0.0
            marker.pose.orientation.y = 0.0
            marker.pose.orientation.z = 0.0
            marker.pose.orientation.w = 1.0
            marker.scale.x = (hull[0][1]-hull[0][0])
            marker.scale.y = (hull[1][1]-hull[1][0])
            marker.scale.z = 0.05
            marker.color.a = 1.0
            if(i==0):
                marker.color.r = 0.0
                marker.color.g = 239.0/255.0
                marker.color.b = 0.0
            else:
                marker.color.r = 1.0
                marker.color.g = 1.0
                marker.color.b = 0.0

            markerArray.markers.append(marker)

        self.vis_pub3.publish(markerArray)        

if __name__ == '__main__':
    rospy.init_node('mpcc_node')
    args = rospy.myargv()[1:]
    racecar_name=args[0]
    waypoint_file=args[1]
    obstacle_file=args[2]
    rospy.sleep(3)
    mpc = MPCC(waypoint_file,obstacle_file,racecar_name=racecar_name)
    r = rospy.Rate(80)
    while not rospy.is_shutdown():
        r.sleep()

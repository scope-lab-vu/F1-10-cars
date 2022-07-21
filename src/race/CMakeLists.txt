cmake_minimum_required(VERSION 3.5)
project(race)


# Default to C++14
if (NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

## Find catkin macros and libraries
## if COMPONENTS list like find_package(catkin REQUIRED COMPONENTS xyz)
## is used, also find other catkin packages
find_package(catkin REQUIRED COMPONENTS
  gazebo_ros
  roscpp
  rospy
  sensor_msgs
  visualization_msgs
  std_msgs
  message_generation
  geometry_msgs
  tf
  roscpp_serialization
  laser_geometry
)

if(NOT DEFINED CMAKE_SUPPRESS_DEVELOPER_WARNINGS)
     set(CMAKE_SUPPRESS_DEVELOPER_WARNINGS 1 CACHE INTERNAL "No dev warnings")
endif()
find_package(PCL REQUIRED)
find_package(Eigen3 REQUIRED)

if (NOT EIGEN3_FOUND)
    # Fallback to cmake_modules
    find_package(cmake_modules REQUIRED)
    find_package(Eigen REQUIRED)
    set(EIGEN3_INCLUDE_DIRS ${EIGEN_INCLUDE_DIRS})
    set(EIGEN3_LIBRARIES ${EIGEN_LIBRARIES})  # Not strictly necessary as Eigen is head only
    # Possibly map additional variables to the EIGEN3_ prefix.
else ()
    set(EIGEN3_INCLUDE_DIRS ${EIGEN3_INCLUDE_DIR})
endif ()

## This macro ensures
## modules and global scripts declared therein get installed
#catkin_python_setup()

#Generate messages in the 'msg' folder
add_message_files(
		FILES
    angle_msg.msg
    prediction.msg
    velocity_msg.msg
		drive_param.msg
		drive_values.msg
    pid_input.msg
    stamped_ttc.msg
    interval.msg
    obstacle_list.msg 
    reach_tube.msg
)


## Generate added messages and services with any dependencies listed here
 generate_messages(
   DEPENDENCIES
   sensor_msgs
 )

catkin_package(
#  INCLUDE_DIRS include
#  LIBRARIES race
  CATKIN_DEPENDS roscpp rospy sensor_msgs std_msgs geometry_msgs gazebo_ros visualization_msgs
#  DEPENDS system_lib
)

###########
## Build ##
###########

## Specify additional locations of header files
## Your package locations should be listed before other locations
# include_directories(include)
include_directories(
  ${catkin_INCLUDE_DIRS}
  ${PCL_INCLUDE_DIRS}
  ${EIGEN3_INCLUDE_DIRS}
)

# add cpp executable
add_executable(laser_converter_node src/laser_to_pointcloud.cpp)
target_link_libraries(laser_converter_node ${PCL_LIBRARIES} ${EIGEN3_LIBRARIES} ${catkin_LIBRARIES}) 


### Install laser converter node 
install(TARGETS 
  laser_converter_node
  DESTINATION lib/${PROJECT_NAME}
)

### Install python nodes
install(PROGRAMS 
scripts/disparity_extender_vanderbilt_gen.py
scripts/follow_lead_gen.py
DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

# Install launch and other files 
install(DIRECTORY
        launch
        rviz
        cfg
        maps
        DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})

  

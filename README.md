# Experiments with F1-10 cars

 This repository includes the controllers working with the f1/10 simulator and the physical car. The code here is cloned from [patricks f1/10 repo](https://github.com/pmusau17/Platooning-F1Tenth). Kindly refer to his repository if new controllers are required for the cars. 

# Controlling the Car in simulation
The car can be controlled manually using a joystick or autonomously using conventional and machine learning controllers.

1. [Simulator Setup](#F1-10-Simulator-Build-and-Run)
2. [Disparity Extender](#Disparity-Extender-Algorithm)
3. [Pure Pursuit](#Pure-Pursuit-Algorithm)
4. [Computer Vision](#Computer-Vision)


# F1-10 Simulator Build and Run

The f1/10 car comes with a [Gazebo](https://gazebosim.org/) based simulator. We run the simulation in docker. The dockerfile for setting up the docker can be found [here](https://github.com/scope-lab-vu/F1-10-cars/tree/main/docker). To install the docker follow the steps discussed below:

Step 1 - Install the suitable [NVIDIA-Docker](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) for your GPU configuration and operating system. The docker is required to run any Machine Learning/Deep Learning based controllers.

Step 2 - Install [Docker](https://docs.docker.com/engine/install/ubuntu/) and [Docker-Compose](https://docs.docker.com/compose/install/) for the operating system on your machine.

Step3 - To build the dockerfile get into the path of this repo and run the following command

```
./build_docker.sh
```

Step 4 - Once the docker build is complete, run the following command to enable the use of graphical user interfaces within the docker containers such as Gazebo and Rviz. This command will give the docker rights to access the X-Server.

```
xhost +si:localuser:root
```
**Optional**: You may also need to run the following commands if the visualization does not work ``` xhost +local:docker ```

step 4 - Next, run the docker using the following command

```
source docker/run_docker.sh (if the machine has a GPU)
or 
source docker/run_docker_cpu.sh (if the machine does not have a GPU)
```
This will take you into the docker. 

Step5 - Source the ROS packages to run ROS in the docker

```
source install/setup.bash
```

**Note**:If you want to open a second window in the docker container, in the second window, use the command
```
docker ps
```
to get the docker container id, and then use
```
docker exec -it ${DOCKER_CONTAINER_ID} bash
```
to enter the container.


# Disparity Extender Algorithm

The disparity extender algorithm was developed at UNC-Chapel Hill. This algorithm was used as the controller for the f1/10 autonomous driving competition in 2019. This controller won the race ultimately. Please read this [blog](https://www.nathanotterness.com/2019/04/the-disparity-extender-algorithm-and.html) from Nathan Otterness et al. to get a complete understanding of the algorithm.

To run this controller in the simulator, run the following commands in two terminals:

Terminal 1:

```
roslaunch race multi_parametrizeable.launch
```
Terminal 2: 

```
roslaunch race multicar_disparity_extender.launch
```

Additional source to learn about the controller https://medium.com/@chardorn/running-an-f1tenth-car-like-a-real-racecar-f5da160d8573

# Pure Pursuit Algorithm
The pure pursuit algorithm was originally proposed by Craig Coulter. The algorithm can be found in his [original paper](https://www.ri.cmu.edu/pub_files/pub3/coulter_r_craig_1992_1/coulter_r_craig_1992_1.pdf). Have a look at this [repo](https://vinesmsuic.github.io/2020/09/29/robotics-purepersuit/) to get a better understanding of the algorithm. 

To run this controller in the simulator, run the following commands in two terminals:

Terminal 1:

```
roslaunch race multi_parametrizeable.launch
```
Terminal 2: 

```
roslaunch race platoon.launch
```

# Computer Vision

ToDo: Patrick has tested out a few end-to-end controllers. We can get to his [repo](https://github.com/pmusau17/Platooning-F1Tenth#ComputerVision) to get them running. 

# Rosbag and Data collection
Run the foolowing command to get the list of topics

```
rostopic list
```

To record data from a topic and store them in to a bag file, run:

```
rosbag record ${TOPIC_NAME_1} ${TOPIC_NAME_2} ...
```

To decode the data from, for example, camera, look at the script src/decoder/decode.py. To decode, change the bag name in the script and then run it:

```
python3 decode.py
```

You can then get the images at the path specified.

# Controlling the Physical Car

Check the [Hardware_Code]() Folder.

# References

1. [Patricks Github Repo](https://github.com/pmusau17/Platooning-F1Tenth) - The base code for our work is taken from patrick. We can tune the algorithms and parameters as required

2. [f1/10 Repo](https://f1tenth.org/) - The tutorials to build, learn and race the car can be found on the repo. The [build manual](https://github.com/scope-lab-vu/F1-10-cars/blob/main/documents/BuildV2.pdf) is also required to debug problems. 










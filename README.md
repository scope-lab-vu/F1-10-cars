# Experiments with F1-10 cars

# Introduction
 
 This repository includes the controllers working with the f1/10 simulator and the physical car. The code here is cloned from [patricks f1/10 repo](https://github.com/pmusau17/Platooning-F1Tenth). Kindly refer to his repository if new controllers are required for the cars. 


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

# Controlling the Car
The car can be controlled manually using a joystick or autonomously using conventional and machine learning controllers.

1. [Teleoperation using Joystick](https://github.com/scope-lab-vu/F1-10-cars/edit/main/README.md#Teleoperatin with Joystick)


# Teleoperatin with Joystick










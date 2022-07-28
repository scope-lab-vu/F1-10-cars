# Controlling the Physical Car

The car can be controlled manually using a joystick or autonomously using conventional and machine learning controllers.

1. [Teleoperation using Joystick](#Teleoperation-with-Joystick)
2. [Disparity Extender](#Disparity-Extender-Algorithm-Car)

# Teleoperation with Joystick

The hardaware testbed can be controlled with a joystick. You can follow these commands to manually control the car

step 1 - Place the car on the ground and run the following command in the terminal

step 2 - Open a terminal on your computer and [SSH](https://github.com/scope-lab-vu/F1-10-cars/blob/main/documents/ssh-car.pdf) into the car from your computer. Once you are in, run [tmux](https://github.com/scope-lab-vu/F1-10-cars/blob/main/documents/ssh-car.pdf) to spawn new terminal sessions over the same SSH connection.

step 3 - In the tmux session, spawn a new window using "Ctrl + B" and C. Then, in the window run ```roscore``` to start ros

step 4 - In the other free terminal (run "Ctrl + B" and w to move between terminals), navigate to the working directory and run source install/setup.bash to source the directory. Then run the following command

```
roslaunch racecar teleop.launch
```

Press the center button on the joystick to control the car. Hold the LB button on the joystick to start controlling the car. Use the left joystick to move the car forward and backward and the right joystick for steering the car. ***Remember*** Always have a hold of the LB button; otherwise the car will stop. 

If there is a problem in using the joystick, look at the f1/10 manual [here](https://github.com/scope-lab-vu/F1-10-cars/blob/main/documents/BuildV2.pdf)

# Disparity Extender Algorithm Car

The disparity extender algorithm was developed at UNC-Chapel Hill. This algorithm was used as the controller for the f1/10 autonomous driving competition in 2019. This controller won the race ultimately. Please read this [blog](https://www.nathanotterness.com/2019/04/the-disparity-extender-algorithm-and.html) from Nathan Otterness et al. to get a complete understanding of the algorithm.

To run this controller in the simulator, ssh into the car and open a terminal. In the terminal type "tmux" to open a tmux session. In the terminal type in "Ctrl + B" and C to create two new terminals. In the first terminal run the following command:

Terminal 1:

```
roscore
```
Now, use "Ctrl + B" and W to move to the second free terminal. Then, run the following command.

Terminal 2: 

```
roslaunch racecar disparity_extender.launch
```

Additional source to learn about the controller https://medium.com/@chardorn/running-an-f1tenth-car-like-a-real-racecar-f5da160d8573











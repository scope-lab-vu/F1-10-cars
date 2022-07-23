#!/bin/bash


# Notes (mostly for me)
# $! Contains the process ID of the most recently executed background pipeline 
# $? This the exit status of the last executed command  
# The linux trap command allows you to catch signals and execute code when they occur
# SIGINT is generated when you type Ctrl-C at the keyboard to interrupt a running script 


# kill -INT $pid sends the "interrupt" signal to the process with process ID pid. 
# However, the process may decide to ignore the signal, or catch the signal and do 
# something before exiting and/or ignore it.


# for future reference generating a random number within a range
# $(shuf -i 0-4 -n 1)


# how many cars to run 
number_of_cars="2 3"

# number of obstacles 
obstacles="0 5"

# Methods
# 0 is end to end
# 1 disparity
# 2 is pp

controller_type="0 1 2"

for alg in $controller_type
do 
    for cars in $number_of_cars
    do
        for obs in $obstacles
        do
            # timeout 
            timeout=60

            # ignore this
            exit_status=0

            # this keeps track of how many experiments we have run
            count=0
            _term() {
              exit_status=$? # = 130 for SIGINT
              echo "Caught SIGINT signal!"
              kill -INT "$child" 2>/dev/null
            }


            trap _term SIGINT

            while [ $count -lt 10 ]
            do
            ((count=count+1)) 
            roslaunch race sim_for_rtreach_uncertain_simplex.launch algorithm:=$alg timeout:=$timeout number_of_cars:=$cars num_obstacles:=$obs experiment_number:=$count & 
                
            child=$!
            wait "$child"
            if [ $exit_status -eq 130 ]; then
                # SIGINT was captured meaning the user
                # wants full stop instead of start_simulation.launch
                # terminating normally from end of episode so...
                echo "stop looping"
                exit 0 
            fi
            echo count: $count
        done
    done
  done
done
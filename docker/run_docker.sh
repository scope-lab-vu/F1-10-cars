#! /bin/bash


#run the docker container
docker container run --rm --privileged --runtime=nvidia -it -e DISPLAY --net=host --env="QT_X11_NO_MITSHM=1" -v /tmp/.X11-unix:/tmp/.X11-unix f1-simulator:v1 bash

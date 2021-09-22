FROM ubuntu:21.04 AS build
ENV TZ=Europe/Rome
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

#install all dependecy
RUN apt-get update -y
RUN apt-get install git -y
RUN apt-get install python -y
RUN apt-get install pip -y

RUN pip install numpy scipy matplotlib casadi redis
RUN pip install --index-url https://google-coral.github.io/py-repo/ tflite_runtime

#download code
RUN git clone https://github.com/bistrulli/3tier-bench-app.git

WORKDIR /3tier-bench-app/3tier-app/controller
 
#start redis
CMD ["redis-server --port 6379"]


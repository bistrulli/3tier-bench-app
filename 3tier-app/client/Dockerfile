FROM ubuntu:21.04 AS build

#install all dependecy
RUN apt-get update -y
RUN apt-get install openjdk-15-jdk -y
RUN apt-get install maven -y
RUN apt-get install git -y
RUN apt-get install python -y
RUN apt-get install pip -y


RUN pip install numpy scipy matplotlib casadi redis
RUN pip install --index-url https://google-coral.github.io/py-repo/ tflite_runtime

#download code
RUN git clone https://github.com/bistrulli/AdaptiveHttpServer.git
RUN git clone https://github.com/bistrulli/3tier-bench-app.git

WORKDIR /AdaptiveHttpServer

RUN mvn package
RUN mvn install

WORKDIR /3tier-bench-app/3tier-app/

RUN mvn package

WORKDIR /3tier-bench-app/3tier-app/client/target

CMD ["sleep","365d"]




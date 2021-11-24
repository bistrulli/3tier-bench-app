FROM ubuntu:21.04 AS build
ENV TZ=Europe/Rome
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

#install all dependecy
RUN apt-get update -y
RUN apt-get install openjdk-15-jdk -y
RUN apt-get install maven -y
RUN apt-get install git -y

RUN echo export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which javac)))) >> ~/.profile
#download code
RUN git clone --branch gke https://github.com/bistrulli/AdaptiveHttpServer.git
RUN git clone --branch gke https://github.com/bistrulli/3tier-bench-app.git

WORKDIR /AdaptiveHttpServer/jni_lib/
RUN sh ./gccInstr.sh
WORKDIR /AdaptiveHttpServer/
RUN mvn clean install

WORKDIR /3tier-bench-app/3tier-app/
RUN mvn clean package

WORKDIR /3tier-bench-app/3tier-app/client/target


EXPOSE 3333

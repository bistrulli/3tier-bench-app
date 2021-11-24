FROM ubuntu:21.04 AS build
ENV TZ=Europe/Rome
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

#install all dependecy
RUN apt-get update -y
RUN apt-get install openjdk-15-jdk -y
RUN apt-get install maven -y
RUN apt-get install git -y

#download code
RUN git clone --branch gke https://github.com/bistrulli/AdaptiveHttpServer.git
RUN git clone --branch gke https://github.com/bistrulli/3tier-bench-app.git

WORKDIR /AdaptiveHttpServer

RUN mvn package
RUN mvn install

WORKDIR /3tier-bench-app/3tier-app/

RUN mvn package

WORKDIR /3tier-bench-app/3tier-app/client/target


EXPOSE 3333

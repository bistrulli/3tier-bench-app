FROM ubuntu:21.04 AS build

#install all dependecy
RUN apt-get update -y
RUN apt-get install openjdk-15-jdk -y
RUN apt-get install maven -y
RUN apt-get install git -y


#download code
RUN git clone https://github.com/bistrulli/AdaptiveHttpServer.git
RUN git clone https://github.com/bistrulli/3tier-bench-app.git

WORKDIR /AdaptiveHttpServer

RUN mvn package
RUN mvn install

WORKDIR /3tier-bench-app/3tier-app/

RUN mvn package

WORKDIR /3tier-bench-app/3tier-app/tier2/target

CMD ["java","-Xmx4G","-jar","tier2-0.0.1-SNAPSHOT-jar-with-dependencies.jar",\
	"--cpuEmu","1","--jedisHost","monitor"]




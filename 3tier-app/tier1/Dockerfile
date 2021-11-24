FROM ubuntu:21.04 AS build

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

WORKDIR /3tier-bench-app/3tier-app/tier1/target

EXPOSE 3000
EXPOSE 13000

#CMD ["java","-Xmx4G","-jar","tier1-0.0.1-SNAPSHOT-jar-with-dependencies.jar",\
#	"--cpuEmu","0","--jedisHost","monitor"]




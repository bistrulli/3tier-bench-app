FROM ubuntu:21.04 AS build
ENV TZ=Europe/Rome
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezones

#install all dependecy
RUN apt-get update -y
RUN apt-get install openjdk-15-jdk -y
RUN apt-get install maven -y
RUN apt-get install git -y
RUN apt-get install htop curl telnet build-essential screen -y

RUN echo export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which javac)))) >> ~/.profile
#download code
RUN git clone --branch gke https://github.com/bistrulli/AdaptiveHttpServer.git
RUN git clone --branch gke https://github.com/bistrulli/3tier-bench-app.git

WORKDIR /AdaptiveHttpServer/jni_lib/
RUN source ~/.profile && sh ./gccInstr.sh
WORKDIR /AdaptiveHttpServer/
RUN mvn clean install

WORKDIR /3tier-bench-app/3tier-app/
RUN mvn clean package

WORKDIR /3tier-bench-app/3tier-app/tier2/target

EXPOSE 3001
EXPOSE 13001

#CMD ["java","-Xmx4G","-jar","tier2-0.0.1-SNAPSHOT-jar-with-dependencies.jar",\
#	"--cpuEmu","1","--jedisHost","monitor"]




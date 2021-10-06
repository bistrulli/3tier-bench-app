# Use existing docker image as a base
FROM alpine

# Download and install dependency
RUN apk add --update redis

#RUN sed -e '/save/ s/^#*/#/' -i /etc/redis.conf
WORKDIR /etc
RUN wget https://gist.githubusercontent.com/ndelitski/0e8d9767894d5e60efa4865659f87a5f/raw/7dafcf179f46752faf4ba24d27956095a4d6f792/redis-no-persistence.conf
RUN echo -e "\nprotected-mode no" >> ./redis-no-persistence.conf

WORKDIR /

# EXPOSE the port to the Host OS
EXPOSE 6379

# Tell the image what command it has to execute as it starts as a container
CMD ["redis-server","--protected-mode","no"]


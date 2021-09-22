# Use existing docker image as a base
FROM alpine

# Download and install dependency
RUN apk add --update redis

# EXPOSE the port to the Host OS
EXPOSE 6379

# Tell the image what command it has to execute as it starts as a container
CMD ["redis-server","--protected-mode","no"]


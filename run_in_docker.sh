#!/usr/bin/env sh
DOCKER_NAME="notebook_madliar"
DOCKER_IMAGE="notebook_madliar_img"

docker stop ${DOCKER_NAME} 2> /dev/null
docker rm ${DOCKER_NAME} 2> /dev/null

docker run -itd --rm \
  --name ${DOCKER_NAME} \
  --net=host \
  -v /data/nvme/notebook_user:/data/notebook_user \
  ${DOCKER_IMAGE}

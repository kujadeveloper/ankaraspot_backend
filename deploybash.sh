#!/bin/bash
VERSION=${1:-default_value}
docker buildx create --use
docker buildx inspect --bootstrap
docker buildx build . --platform linux/amd64,linux/arm64 --tag hakankuja/backend-main:$VERSION --tag hakankuja/backend-main:latest --push
docker buildx prune --all -f
docker rm -f $(docker ps -a -q --filter "name=buildx_buildkit_")
docker volume rm -f $(docker volume ls)
docker system prune -a --volumes -f
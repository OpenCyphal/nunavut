# Toxic Docker

Builds and pushes a docker environment for use with tox testing. This environment contains a series of python versions allowing multi-version tox testing locally and in CI services.

## Build and Push

These instructions are for maintainers with permissions to push to the "uavcan" organization on Docker Hub.

```
docker build .
```
```
docker images

REPOSITORY      TAG            IMAGE ID
toxic           latest         d7ab132649d6
```
```
# We use the range of python environments supported as the version tag.
docker tag d7ab132649d6 uavcan/toxic:py35-py38
docker login --username=yourhubusername
docker push uavcan/toxic:py35-py38
```

## Use locally

```
cd /path/to/mymodule

docker pull uavcan/toxic:py35-py38

docker run --rm -t -v /path/to/myrepo:/repo uavcan/toxic:py35-py38 /bin/sh -c tox
```

On macintosh you'll probably want to optimize osxfs with something like cached or delegated:

```
docker run --rm -t -v /path/to/myrepo:/repo:delegated uavcan/toxic:py35-py38 /bin/sh -c tox
```

See ["Performance tuning for volume mounts"](https://docs.docker.com/docker-for-mac/osxfs-caching/) for details.

Finally, to enter an interactive shell in this container something like this should work:

```
docker run --rm -it -v /path/to/myrepo:/repo uavcan/toxic:py35-py38
```

## Travis CI

You can use this in your .travis.yml like this:

```
language: python

services:
  - docker

before_install:
- submodule update --init --recursive
- docker pull uavcan/toxic:py35-py38

script:
- docker run --rm -v $TRAVIS_BUILD_DIR:/repo uavcan/toxic:py35-py38 /bin/sh -c tox

```

#!/bin/sh
set -e

git clone -b iroha2 https://github.com/hyperledger/iroha-python
(cd iroha-python; docker build . -t iroha:python)

docker run -d \
	-v $PWD/config.json:/config.json \
	-v $PWD/test_case.py:/test_case.py \
	iroha:python \
	python3 test_case.py


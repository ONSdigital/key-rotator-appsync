#!/bin/sh

# This script runs within the terraform docker image
# to pull down the required python libraries, ready
# to be zipped for uploading to AWS

ZIPFILE="key-rotator-appsync.zip"

apk add py3-pip zip
cd lambdas
pip install --ignore-installed --prefix=./ -r requirements.txt
cd lib/python3.9/site-packages
zip -qr $OLDPWD/$ZIPFILE ./*
cd $OLDPWD
zip -jg $ZIPFILE ../lambdas/*

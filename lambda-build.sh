#!/bin/sh

# This script runs within the terraform docker image
# to pull down the required python libraries, ready
# to be zipped for uploading to AWS

ZIPFILE="key-rotator-appsync.zip"

apk install py3-pip
cd lambda
pip install --ignore-installed --prefix=./ -r requirements.txt
cd lib/python3.8/site-packages
zip -qr $OLDPWD/$ZIPFILE ./*
cd $OLDPWD
zip -jg $ZIPFILE ../lambda/*

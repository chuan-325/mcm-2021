#!/bin/bash

cd ../dataset/json/
cat ../../output/tmp/req_line.txt | while read line
do
    eval $line
    sleep 0.3
done

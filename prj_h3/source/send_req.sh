#!/bin/bash

cd ../dataset/json/ || exit
while read -r line
do
    eval "$line"
    sleep 0.3
done < ../../output/tmp/req_line.txt

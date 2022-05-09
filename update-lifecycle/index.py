# -*- coding: utf-8 -*-
import os
import oss2
import json
import urllib.request
import urllib.parse

# 存储桶操作
uploadUrl = "https://upload.aialbum.net"
downloadUrl = "https://download.aialbum.net"
baseUrl = "http://%s.%s" % (os.environ.get('OSS_BUCKET'), os.environ.get('OSS_ENDPOINT'))
auth = oss2.Auth(os.environ.get('ACCESS_KEY_ID'), os.environ.get('ACCESS_KEY_SECRET'))
bucket = oss2.Bucket(auth, os.environ.get('OSS_ENDPOINT'), os.environ.get('OSS_BUCKET'))


def handler(event, context):
    events = json.loads(event.decode("utf-8"))["events"]
    for eveObject in events:
        # 路径处理
        file = eveObject["oss"]["object"]["key"]

        headers = {
            'token': os.environ.get("UPDATE_TOKEN"),
            'update-type': 'lifecycle',
            'object': file.split('/')[-1],
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'lifecycle': "1"
        }

        urllib.request.urlopen(
            urllib.request.Request(
                url="http://%s/photo/update/status"%(os.environ.get("DOMAIN")),
                data=urllib.parse.urlencode(data).encode("utf-8"),
                headers=headers
            )
        )

        bucket.put_object('tmp/' + file.split('/')[-1], file.split('/')[-1].encode("utf-8"))

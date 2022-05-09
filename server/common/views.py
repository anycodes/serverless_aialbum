from django.http import JsonResponse
from django_redis import get_redis_connection

import os
import oss2
import uuid
import time
import json
import random
import hashlib
import urllib.request

# Create your views here.

# 通用配置
DEFAULT = {
    "miniprogram": {
        "appid": os.environ.get('MINIPROGRAM_APPID'),
        "secret": os.environ.get('MINIPROGRAM_SECRET'),
    },
    "update_token": os.environ.get('UPDATE_TOKEN'),
    "aliyun": {
        "access_key_id": os.environ.get('ACCESS_KEY_ID'),
        "access_key_secret": os.environ.get('ACCESS_KEY_SECRET'),
    },
    "oss": {
        "bucket": os.environ.get('OSS_BUCKET'),
        "endpoint": os.environ.get('OSS_ENDPOINT'),
    }
}

# 整体的返回结构
responseBody = lambda body, error=False, requestId=False: JsonResponse({
    "Status": "Error" if error else "Success",
    "Message" if error else "Body": body,
    "RequestId": requestId if requestId else uuid.uuid4(),
})

# 存储桶操作
uploadUrl = "https://upload.aialbum.net"
downloadUrl = "https://download.aialbum.net"
baseUrl = "http://%s.%s" % (DEFAULT['oss']['bucket'], DEFAULT['oss']['endpoint'])
auth = oss2.Auth(DEFAULT['aliyun']['access_key_id'], DEFAULT['aliyun']['access_key_secret'])
bucket = oss2.Bucket(auth, DEFAULT['oss']['endpoint'], DEFAULT['oss']['bucket'])
object = lambda objectName, method="GET", expiry=3600: bucket.sign_url(method, objectName, expiry)
upload = lambda objectName: object(objectName, "PUT").replace(baseUrl, uploadUrl)
download = lambda objectName: object(objectName, method="GET").replace(baseUrl, downloadUrl)

# 获取随机字符串
randomeStr = lambda count=100: "".join(random.sample('zyxwvutsrqponmlkjihgfedcba' * 10, count))

# md5加密
getMD5 = lambda content: hashlib.md5(content.encode("utf-8")).hexdigest()

# 获取格式化时间
getTime = lambda: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

# redis链接
redic_conn = get_redis_connection('default')

# 通用错误
ERROR = {
    "InitializationFailed": "%s",
    "GetOpenIdError": "Could not get OpenId.",
    "SystemError": "Unknown error. Please try again later.",
    "TokenExpired": "The login token has expired.",
    "TokenException": "Login token exception",
    "FriendshipException": "The type of friendship exception",
    "AuthenticationFailed": "You have no permission to operate.",
    "MethodError": "Request method error.",
    "ParameterException": "Parameter acquisition failed.",
    "DBException": "Data storage failed.",
    "UserInformationError": "User information error, please clear the cache and log in again.",
    "AlbumExists": "Album already exists.",
    "AlbumSharedExists": "There are albums with the same name in the shared album.",
    "AlbumCreateFailed": "Album creation failed",
    "PermissionException": "Abnormal operation permission.",
    "AlbumNotExist": "The album does not exist or has been deleted.",
    "AlbumDeletionFailed": "Album deletion failed.",
    "AlbumUpdateFailed": "Album update failed.",
    "AlbumGetFailed": "Album get failed.",
    "StorageFailed": "Storage failure.",
    "AlbumAvailable": "Album name not available.",
    "PhotoNotExist": "The photo does not exist or has been deleted.",
    "PhotoShareNotExist": "The photo share does not exist or has been deleted.",
    "ShareExceeded": "The number of times to get pictures exceeds the limit."
}

# 名人名言
SENTENCE = [
    "青年时种下什么，老年时就收获什么",
    "人并不是因为丽才可爱，而是因为可爱才美丽",
    "人的美德的荣誉比他的财富的荣誉不知大多少倍",
    "人的天职在勇于探索真理",
    "人的知识愈广，人的本身也愈臻完善",
    "生活就是战斗",
    "沉沉的黑夜都是白天的前奏",
    "东天已经到来，春天还会远吗",
    "过去属于死神，未来属于你自己",
    "成功=艰苦劳动+正确的方法+少说空话",
    "放弃时间的人，时间也放弃他",
    "没有方法能使时钏为我敲已过去了的钟点",
    "人的全部本领无非是耐心和时间的混合物",
    "任何节约归根到底是时间的节约",
    "时间就是能力等等发展的地盘",
    "时间是伟大的导师",
    "忘掉今天的人将被明天忘掉",
    "辛勤的蜜蜂永没有时间的悲哀",
    "时间是我的财产，我的田亩是时间",
    "合理安排时间，就等于节约时间",
    "春光不自留，莫怪东风恶",
    "书是人类进步的阶梯",
    "读书时，我愿在每一个美好思想的",
    "书是唯一不死的东西",
    "要多读书，但不要读太多的书",
    "知者乐水，仁者乐山",
    "人最大的无知是不了解自己",
    "道德应当成为迷信的指路明灯",
    "谨慎和自制是智慧的源泉",
    "弄风骄马跑空立，趁兔苍鹰掠地飞",
    "好好学习，天天向上",
    "青春没有选择，只有试一试",
    "一万年太久，只争朝夕",
    "夜来南风起，小麦覆陇黄",
    "天才是1的灵感加99的汗水",
    "志当存高远"
]


# 获取微信小程序 access_token
def getAccessToken():
    url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s" % (
        DEFAULT["miniprogram"]["appid"],
        DEFAULT["miniprogram"]["secret"]
    )
    response_attr = urllib.request.urlopen(url=url).read().decode("utf-8")
    print("getAccessToken POST: ", response_attr)
    return json.loads(response_attr)["access_token"]


# 获取名言警句
def commonSentence(request):
    try:
        return responseBody({"sentence": random.choice(SENTENCE)})
    except Exception as e:
        print("getDailySentence Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')

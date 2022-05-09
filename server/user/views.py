from django.views.decorators.csrf import csrf_exempt

from server.album import Album, UserAlbum
from server.photo.models import Photo, PhotoShare
from server.user.models import User, UserRelationship
from server.common.views import responseBody, getMD5, randomeStr, ERROR, DEFAULT, redic_conn, getAccessToken

import json
import base64
import urllib.parse
import urllib.request

# Create your views here.

# 用户关系与状态
relationship_dict = {"friends": 1, "blacklist": -1}


def checkLogin(code):
    '''
    客户端最多每60分钟登陆一次；code可能是：
       1. 用户传递的'session_key'
       2. 用户传递的'js_code'
     该模块需要先验证'session_key'是否存在，如果不存在再验证js_code
     response: userObject
    '''
    try:
        openid = redic_conn.get(code)
        if not openid:
            try:
                url = "https://api.weixin.qq.com/sns/jscode2session"
                data = {
                    'appid': DEFAULT['miniprogram']['appid'],
                    'secret': DEFAULT['miniprogram']['secret'],
                    'js_code': code,
                    'grant_type': 'authorization_code'
                }
                post_data = urllib.parse.urlencode(data).encode("utf-8")
                request_attr = urllib.request.Request(url=url, data=post_data)
                response_attr = urllib.request.urlopen(request_attr).read().decode("utf-8")
                print("checkLogin POST: ", response_attr)
                openid = json.loads(response_attr)["openid"]
            except Exception as e:
                print("checkLogin ERROR: ", e)
                return {"Error": "SystemError"}
        else:
            openid = openid.decode("utf-8")
        # 写入Redis作为缓存
        redic_conn.setex(code, 3600, openid)
        users = User.objects.filter(openid=openid)
        return {"user": User.objects.create(openid=openid) if not users.exists() else users[0]}
    except Exception as e:
        print("Error: ", e)
        return {"Error": "SystemError"}


@csrf_exempt
def userBasic(request):
    '''
    对用户信息进行基本的操作：
        POST：登陆操作
        GET：获取用户信息
        DELETE：删除用户/注销账号
    :param request:
    :return:
    '''
    try:
        token = request.headers.get('token', None)  # 获取权限Token
        if not token:  # 不传 token 不符合规范，直接报错
            return responseBody(ERROR['ParameterException'], 'ParameterException')
        check_login = checkLogin(token)
        if check_login.get("Error", None):
            return responseBody(ERROR[check_login["Error"]], check_login["Error"])
        user = check_login["user"]
        if request.method == 'GET':
            return responseBody({"username": user.username,
                                 "avatar": user.avatar,
                                 "place": user.place,
                                 "gender": user.gender})
        elif request.method == 'POST':
            # 更新数据到数据库
            user.username = request.POST.get('username')
            user.avatar = request.POST.get('avatar')
            user.place = request.POST.get('place')
            user.gender = request.POST.get('gender')
            user.save()
            return responseBody({"status": "success"})
        elif request.method == 'DELETE':
            # 删除用户关系
            UserRelationship.objects.filter(origin=user[0]).delete()
            UserRelationship.objects.filter(target=user[0]).delete()
            # 修改用户相册状态
            Album.objects.filter(user=user[0]).delete()
            UserAlbum.objects.filter(user=user[0]).delete()
            # 照片与分享的处理
            Photo.objects.filter(upload_user=user[0]).delete()
            PhotoShare.objects.filter(user=user[0]).delete()
            # 删除用户
            user.delete()
            return responseBody({"status": "success"})
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')


def userLoginQRCode(request):
    # 浏览器登陆时，用来获取二维码，二维码有效期十分钟
    try:
        if request.method == 'GET':
            login_token_key = randomeStr(10)
            login_token_value = randomeStr(10)
            login_token = login_token_key + login_token_value
            print('login_token_key: ', login_token_key)
            print('login_token_value: ', login_token_value)
            url = "https://api.weixin.qq.com/wxa/getwxacodeunlimit?access_token=" + getAccessToken()
            data = {
                'scene': 'secret=%s' % (login_token),
                'page': "pages/login/index",
                'env_version': "develop"
            }
            post_data = json.dumps(data).encode("utf-8")
            request_attr = urllib.request.Request(url=url, data=post_data)
            response_attr = urllib.request.urlopen(request_attr).read()
            # 写入Redis作为缓存
            redic_conn.setex(login_token_key, 600, login_token_value)
            return responseBody({"token": getMD5(login_token),
                                 "qrcode": base64.b64encode(response_attr).decode('utf8')})
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')


@csrf_exempt
def userLoginToken(request):
    '''
    电脑端登陆过程中，小程序登陆验证时的请求接口，用于处理openid与token的对应关系
    :param request:
    :return:
    '''
    try:
        if request.method == 'PUT':  # 小程序验证登录
            # 获取权限Token
            token = request.headers.get('token', None)
            login_token_key = request.headers.get('tokenKey', None)
            login_token_value = request.headers.get('tokenValue', None)
            # 不传 token 不符合规范，直接报错
            print([token, login_token_key, login_token_value])
            if None in [token, login_token_key, login_token_value]:
                return responseBody(ERROR['ParameterException'], 'ParameterException')
            # 对参数进行有效期校验
            redis_login_token_value = redic_conn.get(login_token_key)
            if not redis_login_token_value:
                return responseBody(ERROR['TokenExpired'], 'TokenExpired')
            if redis_login_token_value.decode("utf-8") != login_token_value:
                return responseBody(ERROR['TokenException'], 'TokenException')
            check_login = checkLogin(token)
            if check_login.get("Error", None):
                return responseBody(ERROR[check_login["Error"]], check_login["Error"])
            user = check_login["user"]
            login_token = login_token_key + login_token_value
            redic_conn.setex(getMD5(login_token), 3600, user.openid)
            redic_conn.delete(login_token_key)
            return responseBody({"status": "success"})
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')


@csrf_exempt
def userRelationships(request, relationship_type):
    '''
    用户关系接口，用于
        GET：查看用户关系
    '''
    try:
        token = request.headers.get('token', None)  # 获取权限Token
        if not token:  # 不传 token 不符合规范，直接报错
            return responseBody(ERROR['ParameterException'], 'ParameterException')
        check_login = checkLogin(token)
        if check_login.get("Error", None):
            return responseBody(ERROR[check_login["Error"]], check_login["Error"])
        user = check_login["user"]
        getUserInfo = lambda relationship, user: {"id": relationship.id,
                                                  "create_time": relationship.create_time,
                                                  "twoway": relationship.twoway,
                                                  "user": {"id": user.id,
                                                           "username": user.username,
                                                           "avatar": user.avatar,
                                                           "gender": user.gender,
                                                           "place": user.place}}
        if relationship_type not in relationship_dict.keys():
            return responseBody(ERROR['RelationshipException'], 'RelationshipException')
        if request.method == 'GET':  # 获取好友/黑名单信息
            relationship_obj = UserRelationship.objects.filter(origin=user, type=relationship_dict[relationship_type]). \
                select_related('target').only('id', 'create_time', 'twoway', 'target__id', 'target__username',
                                              'target__gender', 'target__place')
            return responseBody([getUserInfo(relationship, relationship.target) for relationship in relationship_obj])
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')


@csrf_exempt
def userRelationshipBasic(request, relationship_type, target_user_id):
    '''
    用户关系接口，用于
        POST：配置用户关系
        DELETE：删除用户关系
    '''
    try:
        token = request.headers.get('token', None)  # 获取权限Token
        if not token:  # 不传 token 不符合规范，直接报错
            return responseBody(ERROR['ParameterException'], 'ParameterException')
        check_login = checkLogin(token)
        if check_login.get("Error", None):
            return responseBody(ERROR[check_login["Error"]], check_login["Error"])
        user = check_login["user"]
        if relationship_type not in relationship_dict.keys():
            return responseBody(ERROR['RelationshipException'], 'RelationshipException')
        target_user = User.objects.filter(id=target_user_id)
        if not target_user.exists():
            return responseBody(ERROR['ParameterException'], 'ParameterException')
        target_user = target_user[0]
        if request.method == 'POST':  # 添加好友/拉黑他人
            # 先查询 UserFriendshiop 是否已经存在了数据
            relationship = UserRelationship.objects.filter(origin=user,
                                                           target=target_user,
                                                           relationship="%s-%s" % (user.id, target_user.id))
            # 增加双向关系
            twoway = False  # 初始化双向关系状态
            twoway_relationship = UserRelationship.objects.filter(origin=target_user,
                                                                  target=user,
                                                                  relationship="%s-%s" % (target_user.id, user.id))
            # 双向关系状态确定
            if twoway_relationship.exists() and relationship_type == 'friends' and twoway_relationship[0].type == 1:
                twoway = True
            twoway_relationship.update(twoway=twoway)
            # 关系创建/更新
            if not relationship.exists():
                UserRelationship.objects.create(origin=user,
                                                target=target_user,
                                                type=relationship_dict[relationship_type],
                                                relationship="%s-%s" % (user.id, target_user.id),
                                                twoway=twoway)
            else:
                relationship.update(type=relationship_dict[relationship_type], twoway=twoway)
            return responseBody({"status": "success"})
        elif request.method == 'DELETE':  # 删除关系
            UserRelationship.objects.filter(origin=user,
                                            target=target_user,
                                            relationship="%s-%s" % (user.id, target_user.id)).delete()
            return responseBody({"status": "success"})
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')

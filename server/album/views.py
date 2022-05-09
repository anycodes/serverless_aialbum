from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

from common.models import Tag
from album.models import Album, UserAlbum
from user.models import User, UserRelationship
from user.views import checkLogin
from common.views import responseBody, ERROR, download

import json

# Create your views here.

getUserInfo = lambda user: {
    "id": user.id,
    "username": user.username,
    "avatar": user.avatar,
    "place": user.place,
    "gender": user.gender
}

getAlbumInfo = lambda album: {
    "id": album.id,
    "description": album.description,
    "name": album.name,
    "user": json.loads(album.user_cache),
    "create_time": album.create_time,
    "record_time": album.record_time,
    "place": album.place,
    "photo_count": album.photo_count,
    "cover": (download('thumbnail/%s' % album.cover.object) if album.cover.thumbnail_status else download(
        'origin/%s' % album.cover.object)) if album.cover and album.cover.lifecycle == 1 else None,
    "tags": json.loads(album.tags_cache or '[]')
}


def albumAlbumViewers(request, album_id):
    try:
        token = request.headers.get('token', None)  # 获取权限Token
        if not token:  # 不传 token 不符合规范，直接报错
            return responseBody(ERROR['ParameterException'], 'ParameterException')
        check_login = checkLogin(token)
        if check_login.get("Error", None):
            return responseBody(ERROR[check_login["Error"]], check_login["Error"])
        user = check_login["user"]
        album = Album.objects.filter(id=album_id)  # 获取相册
        if not album.exists():
            return responseBody(ERROR['AlbumNotExist'], 'AlbumNotExist')
        # 获取用户权限
        if not album.filter(user=user).exists():
            return responseBody(ERROR['AuthenticationFailed'], 'AuthenticationFailed')
        album = album.prefetch_related('viewers').all()
        if request.method == 'GET':
            return responseBody([{"id": viewer.id,
                                  "username": viewer.username,
                                  "avatar": viewer.avatar,
                                  "place": viewer.place,
                                  "gender": viewer.gender} for viewer in album[0].viewers.all()])
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')


@csrf_exempt
def albumUserAlbum(request, album_id):
    try:
        token = request.headers.get('token', None)  # 获取权限Token
        if not token:  # 不传 token 不符合规范，直接报错
            return responseBody(ERROR['ParameterException'], 'ParameterException')
        check_login = checkLogin(token)
        if check_login.get("Error", None):
            return responseBody(ERROR[check_login["Error"]], check_login["Error"])
        user = check_login["user"]
        album = Album.objects.filter(id=album_id)  # 获取相册
        if not album.exists():
            return responseBody(ERROR['AlbumNotExist'], 'AlbumNotExist')
        if not album.filter(user=user).exists():  # 获取用户权限
            return responseBody(ERROR['AuthenticationFailed'], 'AuthenticationFailed')
        if request.method == 'GET':
            getUserAlbum = lambda useralbum, user: {"id": useralbum.id,
                                                    "album": {"id": album[0].id,
                                                              "name": album[0].name},
                                                    "user": {"id": user.id,
                                                             "username": user.username,
                                                             "avatar": user.avatar,
                                                             "place": user.place},
                                                    "acl_type": useralbum.acl_type,
                                                    "create_time": useralbum.create_time}
            getAclUsers = lambda acl_type: [getUserAlbum(eve, eve.user) for eve in
                                            user_album.filter(acl_type=acl_type).prefetch_related('user').all()]
            user_album = UserAlbum.objects.filter(album=album[0]).order_by("-id")
            return responseBody({"acl_type_0": getAclUsers(0),
                                 "acl_type_1": getAclUsers(1),
                                 "acl_type_2": getAclUsers(2)})
        elif request.method == 'POST':
            target_user_id = request.POST.get("user", None)
            acl_type = request.POST.get("acl_type", None)
            if None in [target_user_id, acl_type] or acl_type not in ['0', '1', '2'] or target_user_id == str(user.id):
                return responseBody(ERROR['ParameterException'], 'ParameterException')
            try:  # 判断 target_user 状态
                target_user = User.objects.get(id=target_user_id)
                # 先查询 UserAlbum 是否已经存在了数据
                useralbum = UserAlbum.objects.filter(album=album[0],
                                                     user=target_user,
                                                     useralbum="%s-%s" % (target_user.id, album[0].id))
                if not useralbum.exists():
                    UserAlbum.objects.create(album=album[0],
                                             user=target_user,
                                             acl_type=acl_type,
                                             useralbum="%s-%s" % (target_user.id, album[0].id))
                else:
                    useralbum.update(acl_type=acl_type)
                return responseBody({"status": "success"})
            except Exception as e:
                print("albumUserAlbum Error: ", e)
                return responseBody(ERROR['ParameterException'], 'ParameterException')
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')


@csrf_exempt
def albumBasic(request, album_id):
    try:
        token = request.headers.get('token', None)  # 获取权限Token
        if not token:  # 不传 token 不符合规范，直接报错
            return responseBody(ERROR['ParameterException'], 'ParameterException')
        check_login = checkLogin(token)
        if check_login.get("Error", None):
            return responseBody(ERROR[check_login["Error"]], check_login["Error"])
        user = check_login["user"]
        album = Album.objects.filter(id=album_id)  # 获取相册
        if not album.exists():
            return responseBody(ERROR['AlbumNotExist'], 'AlbumNotExist')
        if request.method == 'GET':
            # ---------------------------------------------
            # * 相册的查看，理论上包括自己、共享的人，不在黑名单的人
            # ---------------------------------------------
            # 先判断相册的权限，如果是自己的相册，则可以直接返回结果
            if album[0].user == user:  # 是自己的相册
                return responseBody(getAlbumInfo(album[0]))
            # 不是自己的相册，需要进一步判断权限
            # 1. 判断用户是否在黑名单，如果在黑名单提示没有权限
            user_relationship = UserRelationship.objects.filter(origin=album[0].user, target=user)
            if user_relationship.filter(type=-1).exists():
                return responseBody(ERROR['AuthenticationFailed'], 'AuthenticationFailed')
            user_album = UserAlbum.objects.filter(album=album[0], user=user)
            if user_album.filter(acl_type=2).exists():
                return responseBody(ERROR['AuthenticationFailed'], 'AuthenticationFailed')
            # 2. 不是自己的相册，也没有在黑名单，需要进一步判断相册权限
            if album[0].acl == 0:  # 私密权限，不对外开放
                return responseBody(ERROR['AlbumNotExist'], 'AlbumNotExist')
            elif album[0].acl == 1:  # 仅针对好友开放
                if not user_relationship.filter(type=1).exists():  # 不存在好友关系
                    return responseBody(ERROR['AlbumNotExist'], 'AlbumNotExist')
            elif album[0].acl == 3:  # 针对特定人开放
                if not user_album.filter(acl_type=0).exists() and not user_album.filter(acl_type=1).exists():
                    return responseBody(ERROR['AlbumNotExist'], 'AlbumNotExist')
            # 将用户添加到观看过的人中
            if not album[0].viewers.filter(id=user.id).exists():
                album[0].viewers.add(user)
            # 如果相册有密码，还需要输入密码
            if album[0].password and album[0].password != request.headers.get('password', None):
                return responseBody(ERROR['AuthenticationFailed'], 'AuthenticationFailed')
            return responseBody(getAlbumInfo(album[0]))
        elif request.method == 'POST':  # 更新相册
            # ---------------------------------------------
            # * 更新相册理论上包括自己，具有更新权限的人
            # * 只要加入了黑名单，无论是当前相册的，还是账号级别的，那么白名单就不会生效
            # ---------------------------------------------
            # 查询用户是否有更新权限
            user_album = UserAlbum.objects.filter(album=album[0], user=user)
            # -1 是所有者；1 是具有管理权限
            if not user_album.filter(acl_type=-1).exists():  # 不是用户自己的相册
                if not user_album.filter(acl_type=1).exists():  # 没有更新权限
                    return responseBody(ERROR['AlbumNotExist'], 'AlbumNotExist')
                # 有更新权限，还需要判断是不是黑名单
                user_relationship = UserRelationship.objects.filter(origin=album[0].user, target=user)
                if user_relationship.exists() and user_relationship[0].type == -1:
                    return responseBody(ERROR['AuthenticationFailed'], 'AuthenticationFailed')
            # 对指定的 Album 进行信息更新
            album.update(description=request.POST.get("description", album[0].description),
                         record_time=request.POST.get("record_time", album[0].record_time),
                         place=request.POST.get("place", album[0].place),
                         password=request.POST.get("password", album[0].password),
                         acl=request.POST.get("acl", album[0].acl))
            # 对标签进行清空，再绑定
            album[0].tags.clear()
            tags = json.loads(request.POST.get("tags", album[0].tags_cache))
            temp_tags = []
            for tag in tags:
                try:
                    temp_tags.append(Tag.objects.get(name=tag))
                except:
                    temp_tags.append(Tag.objects.create(name=tag))
            album[0].tags.add(*temp_tags)
            album.update(tags_cache=json.dumps(tags))
            return responseBody({"status": "success"})
        elif request.method == 'DELETE':  # 删除相册，只能自己删除
            if album.filter(user=user).exists():
                # 用户的 Album 存在，先删除关系中的Album信息
                UserAlbum.objects.filter(album=album[0]).delete()
                # 再删除 Album 信息
                album.delete()
                return responseBody({"status": "success"})
            return responseBody(ERROR['AlbumNotExist'], 'AlbumNotExist')
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')


@csrf_exempt
def albumCreate(request):
    try:
        token = request.headers.get('token', None)  # 获取权限Token
        if not token:  # 不传 token 不符合规范，直接报错
            return responseBody(ERROR['ParameterException'], 'ParameterException')
        check_login = checkLogin(token)
        if check_login.get("Error", None):
            return responseBody(ERROR[check_login["Error"]], check_login["Error"])
        user = check_login["user"]
        if request.method == 'POST':
            # 创建相册
            album = Album.objects.create(name=request.POST.get("name"),
                                         description=request.POST.get("description"),
                                         record_time=request.POST.get("record_time"),
                                         place=request.POST.get("place"),
                                         password=request.POST.get("password"),
                                         acl=request.POST.get("acl", 0),
                                         user=user,
                                         user_cache=json.dumps(getUserInfo(user)),
                                         tags_cache=request.POST.get("tags"))
            # 增加标签信息
            tags = json.loads(request.POST.get("tags", '[]'))
            temp_tags = []
            for tag in tags:
                try:
                    tag_obj = Tag.objects.get(name=tag)
                except:
                    tag_obj = Tag.objects.create(name=tag)
                temp_tags.append(tag_obj)
            album.tags.add(*temp_tags)
            # 增加用户相册关系
            UserAlbum.objects.create(album=album, user=user, acl_type=-1, useralbum="%s-%s" % (user.id, album.id))
            return responseBody({"status": "success"})
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')


def albumAlbums(request):
    # try:
    token = request.headers.get('token', None)  # 获取权限Token
    if not token:  # 不传 token 不符合规范，直接报错
        return responseBody(ERROR['ParameterException'], 'ParameterException')
    check_login = checkLogin(token)
    if check_login.get("Error", None):
        return responseBody(ERROR[check_login["Error"]], check_login["Error"])
    user = check_login["user"]
    if request.method == 'GET':
        # 获取相册列表
        albums = UserAlbum.objects.filter(user=user).filter(~Q(acl_type=2)) \
            .select_related('album', 'album__cover').only('album__id',
                                                          'album__description',
                                                          'album__name',
                                                          'album__user_cache',
                                                          'album__create_time',
                                                          'album__record_time',
                                                          'album__place',
                                                          'album__photo_count',
                                                          'album__cover__object',
                                                          'album__cover__thumbnail_status',
                                                          'album__tags_cache',
                                                          'id',
                                                          'acl_type')
        return responseBody([{"user_album": {"id": useralbum.id,
                                             "acl_type": useralbum.acl_type},
                              "album": getAlbumInfo(useralbum.album)} for useralbum in albums])
    return responseBody(ERROR['MethodError'], 'MethodError')
    # except Exception as e:
    #     print("Error: ", e)
    #     return responseBody(ERROR['SystemError'], 'SystemError')

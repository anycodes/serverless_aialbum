from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

from user.models import UserRelationship
from user.views import checkLogin
from album.views import getUserInfo
from common.views import responseBody, ERROR, upload, download, randomeStr, DEFAULT
from photo.models import Photo, PhotoShare
from album.models import Album, UserAlbum

import json

# Create your views here.

# 分享类型与状态
share_type_dict = {
    0: '不限制查看',
    1: '每个人可查看一次',
    2: '仅好友可查看',
    3: '仅好友可查看一次'
}

getPhotoInfo = lambda photo: {
    "id": photo.id,
    "type": photo.type,
    "upload_time": photo.upload_time,
    "object": {
        "origin": download('origin/%s' % photo.object),
        "thumbnail": download('thumbnail/%s' % photo.object) if photo.thumbnail_status else download(
            'origin/%s' % photo.object),
    },
    "description": photo.description,
    "create_time": {
        "create_time": photo.create_time,
        "year": photo.create_time.year if photo.create_time else None,
        "month": photo.create_time.month if photo.create_time else None,
        "day": photo.create_time.day if photo.create_time else None,
    },
    "location": {
        "longitude": photo.longitude,
        "latitude": photo.latitude
    }
}

getPhotoShareInfo = lambda photo_share: {
    "id": photo_share.id,
    "photo": getPhotoInfo(photo_share.photo),
    "create_time": photo_share.create_time,
    "share_type": share_type_dict[photo_share.share_type],
    "token": photo_share.token,
    "password": photo_share.password
}


def photoPhotoSharePhoto(request):
    try:
        share = request.headers.get('share', None)  # 获取权限Share
        photo_share = PhotoShare.objects.filter(token=share).select_related('photo')
        if not photo_share.exists():
            return responseBody(ERROR['PhotoShareNotExist'], 'PhotoShareNotExist')
        if request.method == 'GET':
            if photo_share[0].share_type == 0:  # 如果是不限制查看：
                if photo_share[0].password and photo_share[0].password != request.headers.get('password', None):
                    return responseBody(ERROR['PermissionException'], 'PermissionException')
                photo_share[0].photo.view_count = photo_share[0].photo.view_count + 1
                photo_share[0].photo.save()
                return responseBody(getPhotoShareInfo(photo_share[0]))
            token = request.headers.get('token', None)  # 获取权限Token
            if not token:  # 不传 token 不符合规范，直接报错
                return responseBody(ERROR['ParameterException'], 'ParameterException')
            check_login = checkLogin(token)
            if check_login.get("Error", None):
                return responseBody(ERROR[check_login["Error"]], check_login["Error"])
            user = check_login["user"]
            # 每个人可以查看一次
            if photo_share[0].share_type == 1:
                if photo_share[0].viewers.filter(id=user.id).exists():
                    return responseBody(ERROR['ShareExceeded'], 'ShareExceeded')
                if photo_share[0].password and photo_share[0].password != request.headers.get('password', None):
                    return responseBody(ERROR['PermissionException'], 'PermissionException')
                photo_share[0].viewers.add(user)
                photo_share[0].photo.view_count = photo_share[0].photo.view_count + 1
                photo_share[0].photo.save()
                return responseBody(getPhotoShareInfo(photo_share[0]))
            # 仅好友可以查看
            if not UserRelationship.objects.filter(origin=photo_share[0].user, target=user, type=1).exists():
                return responseBody(ERROR['ParameterException'], 'ParameterException')
            if photo_share[0].share_type == 2:
                if photo_share[0].password and photo_share[0].password != request.headers.get('password', None):
                    return responseBody(ERROR['PermissionException'], 'PermissionException')
                if not photo_share[0].viewers.filter(id=user.id).exists():
                    photo_share[0].viewers.add(user)
                photo_share[0].photo.view_count = photo_share[0].photo.view_count + 1
                photo_share[0].photo.save()
                return responseBody(getPhotoShareInfo(photo_share[0]))
            if photo_share[0].share_type == 3:
                if photo_share[0].viewers.filter(id=user.id).exists():
                    return responseBody(ERROR['ShareExceeded'], 'ShareExceeded')
                if photo_share[0].password and photo_share[0].password != request.headers.get('password', None):
                    return responseBody(ERROR['PermissionException'], 'PermissionException')
                photo_share[0].viewers.add(user)
                photo_share[0].photo.view_count = photo_share[0].photo.view_count + 1
                photo_share[0].photo.save()
                return responseBody(getPhotoShareInfo(photo_share[0]))
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')


def photoPhotoShareViewers(request, photo_share_id):
    try:
        token = request.headers.get('token', None)  # 获取权限Token
        if not token:  # 不传 token 不符合规范，直接报错
            return responseBody(ERROR['ParameterException'], 'ParameterException')
        check_login = checkLogin(token)
        if check_login.get("Error", None):
            return responseBody(ERROR[check_login["Error"]], check_login["Error"])
        user = check_login["user"]
        photo_share = PhotoShare.objects.filter(id=photo_share_id, user=user).prefetch_related('viewers')
        if not photo_share.exists():
            return responseBody(ERROR['PhotoShareNotExist'], 'PhotoShareNotExist')
        if request.method == 'GET':  # 获取分享查看者列表
            return responseBody([getUserInfo(viewer) for viewer in photo_share[0].viewers.all()])
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')


def photoPhotoShares(request):
    try:
        token = request.headers.get('token', None)  # 获取权限Token
        if not token:  # 不传 token 不符合规范，直接报错
            return responseBody(ERROR['ParameterException'], 'ParameterException')
        check_login = checkLogin(token)
        if check_login.get("Error", None):
            return responseBody(ERROR[check_login["Error"]], check_login["Error"])
        user = check_login["user"]
        if request.method == 'GET':
            photo_shares = PhotoShare.objects.filter(user=user).select_related('photo').order_by('-id')
            return responseBody([getPhotoShareInfo(photo_share) for photo_share in photo_shares])
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')


@csrf_exempt
def photoPhotoShareCreate(request, photo_id):
    try:
        token = request.headers.get('token', None)  # 获取权限Token
        if not token:  # 不传 token 不符合规范，直接报错
            return responseBody(ERROR['ParameterException'], 'ParameterException')
        check_login = checkLogin(token)
        if check_login.get("Error", None):
            return responseBody(ERROR[check_login["Error"]], check_login["Error"])
        user = check_login["user"]
        photo = Photo.objects.filter(id=photo_id, upload_user=user, lifecycle=1)
        if not photo.exists():
            return responseBody(ERROR['PhotoNotExist'], 'PhotoNotExist')
        if request.method == 'POST':  # 上传照片
            temp_token = randomeStr(150)
            temp_password = randomeStr(6) if request.POST.get('password', None) == '1' else None
            share_type = request.POST.get('share_type', '0')
            if share_type not in ['0', '1', '2', '3']:
                return responseBody(ERROR['ParameterException'], 'ParameterException')
            PhotoShare.objects.create(user=user,
                                      photo=photo[0],
                                      token=temp_token,
                                      password=temp_password,
                                      share_type=share_type)
            return responseBody({"share_token": temp_token})
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')


@csrf_exempt
def photoPhotoShareBasic(request, photo_share_id):
    try:
        token = request.headers.get('token', None)  # 获取权限Token
        if not token:  # 不传 token 不符合规范，直接报错
            return responseBody(ERROR['ParameterException'], 'ParameterException')
        check_login = checkLogin(token)
        if check_login.get("Error", None):
            return responseBody(ERROR[check_login["Error"]], check_login["Error"])
        user = check_login["user"]
        photo_share = PhotoShare.objects.filter(id=photo_share_id, user=user).select_related('photo')
        if not photo_share.exists():
            return responseBody(ERROR['PhotoShareNotExist'], 'PhotoShareNotExist')
        if request.method == 'GET':  # 查看
            return responseBody(getPhotoShareInfo(photo_share[0]))
        elif request.method == 'DELETE':  # 删除
            photo_share.delete()
            return responseBody({"status": "success"})
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')


def photoPhotoViewers(request, photo_id):
    try:
        token = request.headers.get('token', None)  # 获取权限Token
        if not token:  # 不传 token 不符合规范，直接报错
            return responseBody(ERROR['ParameterException'], 'ParameterException')
        check_login = checkLogin(token)
        if check_login.get("Error", None):
            return responseBody(ERROR[check_login["Error"]], check_login["Error"])
        user = check_login["user"]
        photo = Photo.objects.filter(id=photo_id, upload_user=user, lifecycle=1).prefetch_related('viewers')
        if not photo.exists():
            return responseBody(ERROR['PhotoNotExist'], 'PhotoNotExist')
        if request.method == 'GET':  # 获取照片列表
            return responseBody([getUserInfo(viewer) for viewer in photo[0].viewers.all()])
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')



def photoPhotos(request):
    try:
        token = request.headers.get('token', None)  # 获取权限Token
        if not token:  # 不传 token 不符合规范，直接报错
            return responseBody(ERROR['ParameterException'], 'ParameterException')
        check_login = checkLogin(token)
        if check_login.get("Error", None):
            return responseBody(ERROR[check_login["Error"]], check_login["Error"])
        user = check_login["user"]
        photos = Photo.objects.filter(upload_user=user)
        if request.method == 'GET':
            photo_type = request.headers.get('photo-type', 'recycle')
            if photo_type == 'recycle':
                result_photos = [getPhotoInfo(photo) for
                                 photo in photos.filter(lifecycle=-1).only('id', 'type', 'upload_time', 'object',
                                                                           'description', 'create_time',
                                                                           'longitude', 'latitude',
                                                                           'thumbnail_status').order_by('-delete_time')]
            else:
                temp_list = []
                result_photos = []
                # 先查album
                albums = UserAlbum.objects.filter(user=user).filter(~Q(acl_type=2)).select_related(
                    'album').prefetch_related('album__pictures').filter(~Q(album__pictures__longitude=None))
                # 再查photo
                owner_photos = Photo.objects.filter(upload_user=user, lifecycle=1).filter(~Q(longitude=None))
                if photo_type == 'location':
                    # 先查album
                    albums = albums.filter(~Q(album__pictures__longitude=None))
                    # 再查photo
                    owner_photos = owner_photos.filter(~Q(longitude=None))
                albums = albums.only('album__pictures__id', 'album__pictures__type', 'album__pictures__upload_time',
                                     'album__pictures__object', 'album__pictures__description',
                                     'album__pictures__create_time', 'album__pictures__longitude',
                                     'album__pictures__latitude', 'album__pictures__thumbnail_status').all()
                for album in albums:
                    for photo in album.album.pictures.all():
                        if photo.id not in temp_list:
                            result_photos.append(getPhotoInfo(photo))
                            temp_list.append(photo.id)
                owner_photos = owner_photos.only('id', 'type', 'upload_time', 'object', 'description',
                                                 'create_time', 'longitude', 'latitude', 'thumbnail_status',
                                                 'ai_description').order_by('-id')
                for photo in owner_photos:
                    if photo.id not in temp_list:
                        result_photos.append(getPhotoInfo(photo))
                        temp_list.append(photo.id)
                return responseBody(result_photos)
            return responseBody(result_photos)
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')


@csrf_exempt
def photoBasic(request, photo_id):
    try:
        token = request.headers.get('token', None)  # 获取权限Token
        if not token:  # 不传 token 不符合规范，直接报错
            return responseBody(ERROR['ParameterException'], 'ParameterException')
        check_login = checkLogin(token)
        if check_login.get("Error", None):
            return responseBody(ERROR[check_login["Error"]], check_login["Error"])
        user = check_login["user"]
        photo_recycle = True if request.headers.get('photo_type', 'recycle') == 'recycle' else False
        photo = Photo.objects.filter(id=photo_id, upload_user=user, lifecycle=-1 if photo_recycle else 1)
        if not photo.exists():
            return responseBody(ERROR['PhotoNotExist'], 'PhotoNotExist')
        if request.method == 'GET':  # 查看照片
            photo.update(view_count=photo[0].view_count + 1)
            return responseBody(getPhotoInfo(photo[0]))
        elif request.method == 'PUT':  # 更新信息
            if photo_recycle and request.headers.get('lifecycle', None) == '1':
                # 从回收站恢复照片
                photo.update(lifecycle=1)
            else:
                # 对正常图片增加description
                photo.update(description=request.POST.get("description", None))
            return responseBody({"status": "success"})
        elif request.method == 'DELETE':  # 删除照片
            # 先删除分享图片
            PhotoShare.objects.filter(photo=photo[0]).delete()
            # 从回收站删除-> 永久删除，状态-2
            # 从正常图片删除-> 放入回收站，状态-1
            photo.update(lifecycle=-2 if photo_recycle else -1)
            return responseBody({"status": "success"})
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')


@csrf_exempt
def photoUpload(request):
    try:
        token = request.headers.get('token', None)  # 获取权限Token
        if not token:  # 不传 token 不符合规范，直接报错
            return responseBody(ERROR['ParameterException'], 'ParameterException')
        check_login = checkLogin(token)
        if check_login.get("Error", None):
            return responseBody(ERROR[check_login["Error"]], check_login["Error"])
        user = check_login["user"]
        if request.method == 'POST':  # 上传照片
            temp_object = randomeStr(150)  # 获取上传照片的信息
            temp_type = request.POST.get("type", 0)
            if temp_type not in [0, 1]:  # type必须明确
                return responseBody(ERROR['ParameterException'], 'ParameterException')
            # 创建图片
            Photo.objects.create(type=temp_type,
                                 upload_user=user,
                                 object=temp_object,
                                 description=request.POST.get("description", None),
                                 lifecycle=0,
                                 view_count=0)
            return responseBody({"url": upload('origin/%s' % temp_object)})
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')


@csrf_exempt
def albumAlbumPhotos(request, album_id):
    '''
    对相册下的照片进行处理
        请求方法 GET：获取相册下的照片
        请求方法 POST：
            header参数：update_type
                - unbound_photo：对相册下的照片进行解绑
                - bind_photo：绑定新的照片到相册
                - set_cover：设置封面信息
    '''
    try:
        token = request.headers.get('token', None)  # 获取权限Token
        if not token:  # 不传 token 不符合规范，直接报错
            return responseBody(ERROR['ParameterException'], 'ParameterException')
        check_login = checkLogin(token)
        if check_login.get("Error", None):
            return responseBody(ERROR[check_login["Error"]], check_login["Error"])
        user = check_login["user"]
        album = Album.objects.filter(id=album_id).prefetch_related('pictures')  # 获取相册
        if not album.exists():
            return responseBody(ERROR['AlbumExists'], 'AlbumExists')
        if request.method == 'GET':
            # ---------------------------------------------
            # * 相册的查看，理论上包括自己、共享的人，不在黑名单的人
            # ---------------------------------------------
            # 先判断相册的权限，如果是自己的相册，则可以直接返回结果
            if album[0].user == user:  # 是自己的相册
                return responseBody([getPhotoInfo(photo) for photo in album[0].pictures.all()])
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
                return responseBody(ERROR['AlbumExists'], 'AlbumExists')
            elif album[0].acl == 1:  # 仅针对好友开放
                if not user_relationship.filter(type=1).exists():  # 不存在好友关系
                    return responseBody(ERROR['AlbumExists'], 'AlbumExists')
            elif album[0].acl == 3:  # 针对特定人开放
                if not user_album.filter(acl_type=0).exists() and not user_album.filter(acl_type=1).exists():
                    return responseBody(ERROR['AlbumExists'], 'AlbumExists')
            # 将用户添加到观看过的人中
            if not album[0].viewers.filter(id=user.id).exists():
                album[0].viewers.add(user)
            # 如果相册有密码，还需要输入密码
            if album[0].password and album[0].password != request.headers.get('password', None):
                return responseBody(ERROR['AuthenticationFailed'], 'AuthenticationFailed')
            return responseBody([getPhotoInfo(photo) for photo in album[0].pictures.all()])
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
                    return responseBody(ERROR['AlbumExists'], 'AlbumExists')
                # 有更新权限，还需要判断是不是黑名单
                user_relationship = UserRelationship.objects.filter(origin=album[0].user, target=user)
                if user_relationship.exists() and user_relationship[0].type == -1:
                    return responseBody(ERROR['AuthenticationFailed'], 'AuthenticationFailed')
            # 对指定的 Album 进行信息更新
            update_type = request.headers.get('update-type', 'information')
            if update_type == 'information':  # 更新基本信息
                description = request.POST.get("description")
                album.update(description=description)
                return responseBody({"status": "success"})
            elif update_type == 'bind_photo':  # 绑定图片
                photos = json.loads(request.POST.get("photos", '[]'))
                photos_object = Photo.objects.in_bulk(photos)
                album[0].pictures.add(*[photos_object[eve] for eve in photos_object])
                # 更新图片数量
                Album.objects.filter(id=album_id).update(photo_count=Album.objects.get(id=album_id).pictures.count())
                return responseBody({"status": "success"})
            elif update_type == 'set_cover':  # 配置相册封面
                cover = request.POST.get("cover", None)
                if not cover:
                    return responseBody(ERROR['ParameterException'], 'ParameterException')
                photo = album[0].pictures.filter(id=cover)
                if not photo.exists():
                    return responseBody(ERROR['PhotoNotExist'], 'PhotoNotExist')
                album.update(cover=photo[0])
                return responseBody({"status": "success"})
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')


@csrf_exempt
def photoUpdateStatus(request):
    '''
    内部接口，主要用户图片状态更新
        请求方法 POST：
            header参数：update_type
                - lifecycle：对生命周期进行调整
                - thumbnail：对缩略图状态调整
                - image_caption：image caption之后的描述信息调整
                - base_information：对经纬度、照片拍摄时间调整
    '''
    try:
        # 获取权限Token
        token = request.headers.get('token', None)
        # 对内部接口参数进行权限鉴定
        if token != DEFAULT['update_token']:
            return responseBody(ERROR['AuthenticationFailed'], 'AuthenticationFailed')

        object = request.headers.get('object', None)
        photo = Photo.objects.filter(object=object)

        if request.method == 'POST':
            update_type = request.headers.get('update-type', "lifecycle")
            if update_type == 'lifecycle':
                photo.update(lifecycle=1 if request.POST.get("lifecycle", None) == '1' else 0)
            elif update_type == 'thumbnail':
                photo.update(thumbnail_status=True if request.POST.get("thumbnail", None) == '1' else False)
            elif update_type == 'image_caption':
                photo.update(ai_description=request.POST.get("ai_description", None))
            elif update_type == 'image_type':
                photo.update(type=request.POST.get("image_type", '0'))
            elif update_type == 'base_information':
                photo.update(longitude=request.POST.get("longitude", None),
                             latitude=request.POST.get("latitude", None),
                             create_time=request.POST.get("create_time", None))
            return responseBody({"status": "success"})
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')


@csrf_exempt
def photoSearch(request):
    try:
        # 获取权限Token
        token = request.headers.get('token', None)
        # 不传 token 不符合规范，直接报错
        if not token:
            return responseBody(ERROR['ParameterException'], 'ParameterException')
        check_login = checkLogin(token)
        if check_login.get("Error", None):
            return responseBody(ERROR[check_login["Error"]], check_login["Error"])
        user = check_login["user"]
        if request.method == 'GET':
            keyword = request.GET.get('keyword', None)
            getCount = lambda temp_information, keyword: len(set(temp_information) & keyword)
            temp_list = []
            result_photos = []
            # 先查album
            albums = UserAlbum.objects.filter(user=user).filter(~Q(acl_type=2)).select_related('album').prefetch_related(
                'album__pictures')
            # 再查photo
            owner_photos = Photo.objects.filter(upload_user=user, lifecycle=1)
            if keyword:
                keyword = set(keyword)
                albums = albums.only('album__pictures__id', 'album__pictures__type', 'album__pictures__upload_time',
                                     'album__pictures__object', 'album__pictures__description',
                                     'album__pictures__create_time', 'album__pictures__longitude',
                                     'album__pictures__latitude', 'album__pictures__thumbnail_status',
                                     'album__pictures__ai_description', 'album__place', 'album__name',
                                     'album__description', 'album__tags_cache').all()
                for album in albums:
                    for photo in album.album.pictures.all():
                        if photo.id not in temp_list:
                            temp_information = getPhotoInfo(photo)
                            temp_information['score'] = getCount("%s %s %s %s %s" % (
                            str(album.album.name), str(album.album.place), str(album.album.description),
                            str(album.album.tags_cache), str(photo.ai_description)), keyword)
                            result_photos.append(temp_information)
                            temp_list.append(photo.id)
                owner_photos = owner_photos.only('id', 'type', 'upload_time', 'object', 'description',
                                                 'create_time', 'longitude', 'latitude', 'thumbnail_status',
                                                 'ai_description').order_by('-id')
                for photo in owner_photos:
                    if photo.id not in temp_list:
                        temp_information = getPhotoInfo(photo)
                        temp_information['score'] = getCount(str(photo.ai_description), keyword)
                        result_photos.append(temp_information)
                        temp_list.append(photo.id)
                return responseBody(sorted(result_photos, key=lambda e: e.__getitem__('score'), reverse=True))
            else:
                albums = albums.only('album__pictures__id', 'album__pictures__type', 'album__pictures__upload_time',
                                     'album__pictures__object', 'album__pictures__description',
                                     'album__pictures__create_time', 'album__pictures__longitude',
                                     'album__pictures__latitude', 'album__pictures__thumbnail_status').all()
                for album in albums:
                    for photo in album.album.pictures.all():
                        if photo.id not in temp_list:
                            result_photos.append(getPhotoInfo(photo))
                            temp_list.append(photo.id)
                owner_photos = owner_photos.only('id', 'type', 'upload_time', 'object', 'description',
                                                 'create_time', 'longitude', 'latitude', 'thumbnail_status',
                                                 'ai_description').order_by('-id')
                for photo in owner_photos:
                    if photo.id not in temp_list:
                        result_photos.append(getPhotoInfo(photo))
                        temp_list.append(photo.id)
                return responseBody(result_photos)
        return responseBody(ERROR['MethodError'], 'MethodError')
    except Exception as e:
        print("Error: ", e)
        return responseBody(ERROR['SystemError'], 'SystemError')

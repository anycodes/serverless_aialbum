"""aialbum URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from server.user import userBasic, userLoginQRCode, userLoginToken, userRelationshipBasic, userRelationships
from server.common.views import commonSentence
from server.album import albumBasic, albumCreate, albumUserAlbum, albumAlbumViewers, albumAlbums
from server.photo import photoPhotoSharePhoto, photoPhotoShareViewers, photoPhotoShares, photoPhotoShareCreate, \
    photoPhotoShareBasic, photoPhotoViewers, photoPhotos, photoBasic, photoUpload, albumAlbumPhotos, \
    photoUpdateStatus, photoSearch

urlpatterns = [
    # path('admin/', admin.site.urls),
    # 通用接口
    path('sentence', commonSentence),  # 每日名言
    # 用户接口
    path('user', userBasic),  # 用户注册&登陆&更新信息&注销
    path('qrcode', userLoginQRCode),  # 获取用户登录二维码（电脑端登陆）
    path('token', userLoginToken),  # 对token进行校验（电脑端登陆时所需）
    path('user/<relationship_type>/relationship', userRelationships),  # 获取用户关系，好友&黑名单
    path('user/<relationship_type>/relationship/target/<target_user_id>', userRelationshipBasic),  # 好友&黑名单，删除好友
    # 相册接口
    path('albums', albumAlbums),  # 获取相册列表
    path('album', albumCreate),  # 创建相册
    path('album/<int:album_id>', albumBasic),  # 查看相册&删除相册&更新相册
    path('album/<int:album_id>/viewers', albumAlbumViewers),  # 获取查看相册的浏览者
    path('album/<int:album_id>/acl', albumUserAlbum),  # 相册权限
    path('album/<int:album_id>/photos', albumAlbumPhotos),  # 获取相册图片&更新相册图片信息
    # 照片接口
    path('shares', photoPhotoShares),  # 获取分享列表
    path('share/code', photoPhotoSharePhoto),  # 获取其他人分享的图片/视频
    path('share/<photo_share_id>', photoPhotoShareBasic),  # 查看分享&删除分享
    path('share/<photo_share_id>/viewers', photoPhotoShareViewers),  # 获取查看分享的浏览者
    path('photos', photoPhotos),  # 获取照片列表
    path('photo', photoUpload),  # 创建照片
    path('photo/<photo_id>', photoBasic),  # 查看照片&删除照片&更新照片
    path('photo/<photo_id>/share', photoPhotoShareCreate),  # 创建分享
    path('photo/<photo_id>/viewers', photoPhotoViewers),  # 获取查看照片的浏览者
    path('photo/update/status', photoUpdateStatus),  # 内部接口
    path('search', photoSearch),  # 搜索接口
]

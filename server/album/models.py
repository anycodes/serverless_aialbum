from django.db import models
from photo.models import Photo
from user.models import User
from common.models import Tag


# Create your models here.


# 相册表
class Album(models.Model):
    ACL_STATUE = (
        (0, '私密'),
        (1, '共享给好友'),
        (2, '共享给所有人'),
        (3, '共享给指定人')
    )
    id = models.AutoField(primary_key=True, verbose_name="编号")
    name = models.CharField(max_length=191, verbose_name="相册名")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="创建者")
    user_cache = models.TextField(verbose_name="创建者缓存", null=True, blank=True)
    description = models.TextField(blank=True, null=True, verbose_name="相册描述")
    create_time = models.DateTimeField(auto_created=True, auto_now_add=True, verbose_name="创建时间")
    record_time = models.DateTimeField(blank=True, null=True, verbose_name="记录时间")
    place = models.CharField(max_length=191, verbose_name="记录地点", null=True, blank=True)
    password = models.CharField(max_length=191, blank=True, null=True, verbose_name="相册密码")
    acl = models.IntegerField(choices=ACL_STATUE, default=0, verbose_name="权限")
    photo_count = models.IntegerField(default=0, verbose_name="照片数量")
    pictures = models.ManyToManyField(Photo, verbose_name="图片")
    cover = models.ForeignKey(Photo, blank=True, null=True, related_name='album_photo_cover', on_delete=models.CASCADE, verbose_name="封面")
    tags = models.ManyToManyField(Tag, verbose_name="标签")
    tags_cache = models.TextField(verbose_name="标签缓存", null=True, blank=True)
    viewers = models.ManyToManyField(User, related_name='album_user_viewers', verbose_name="查看者")
    remark = models.TextField(verbose_name="备注", null=True, blank=True)

    class Meta:
        verbose_name = "相册"
        verbose_name_plural = verbose_name
        ordering = ["id"]

    def __str__(self):
        return self.name


# 用户相册关系
class UserAlbum(models.Model):
    ACL_TYPE = (
        (-1, '所有者'),
        (0, '查看'),
        (1, '管理'),
        (2, '屏蔽'),
    )
    id = models.AutoField(primary_key=True, verbose_name="编号")
    album = models.ForeignKey(Album, on_delete=models.CASCADE, verbose_name="相册")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    acl_type = models.IntegerField(choices=ACL_TYPE, default=-1, verbose_name="权限")
    useralbum = models.CharField(max_length=191, unique=True, verbose_name="关系Token")
    create_time = models.DateTimeField(auto_created=True, auto_now_add=True, verbose_name="创建时间")
    remark = models.TextField(verbose_name="备注", null=True, blank=True)

    class Meta:
        verbose_name = "用户相册关系"
        verbose_name_plural = verbose_name
        ordering = ["id"]

    def __str__(self):
        return str(self.user.id) + ' - ' + self.album.name

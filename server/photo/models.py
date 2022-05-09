from django.db import models
from server.user.models import User


# Create your models here.


# 照片表
class Photo(models.Model):
    LIFECYCLE_STATUE = (
        (-2, '已删除'),
        (-1, '回收站'),
        (0, '待上传'),
        (1, '可用')
    )
    PHOTO_TYPE = (
        (0, '图片'),
        (1, '视频')
    )
    id = models.AutoField(primary_key=True, verbose_name="编号")
    type = models.IntegerField(choices=PHOTO_TYPE, default=0, verbose_name="类型")
    upload_time = models.DateTimeField(auto_created=True, auto_now_add=True, verbose_name="上传时间")
    upload_user = models.ForeignKey(User, related_name='photo_user_upload_user', on_delete=models.CASCADE, verbose_name="上传用户")
    object = models.CharField(max_length=191, unique=True, verbose_name="object")
    thumbnail_status = models.BooleanField(default=False, verbose_name="压缩状态")
    description = models.CharField(max_length=191, blank=True, null=True, verbose_name="照片描述")
    ai_description = models.TextField(blank=True, null=True, verbose_name="机器描述")
    lifecycle = models.IntegerField(choices=LIFECYCLE_STATUE, default=0, verbose_name="状态")
    delete_time = models.DateTimeField(blank=True, null=True, verbose_name="创建时间")
    viewers = models.ManyToManyField(User, related_name='photo_user_viewers', verbose_name="查看者")
    view_count = models.IntegerField(default=0, verbose_name="查看次数")
    create_time = models.DateTimeField(blank=True, null=True, verbose_name="拍摄时间")
    longitude = models.FloatField(blank=True, null=True, verbose_name="经度")
    latitude = models.FloatField(blank=True, null=True, verbose_name="纬度")
    remark = models.TextField(verbose_name="备注", null=True, blank=True)

    class Meta:
        verbose_name = "照片"
        verbose_name_plural = verbose_name
        ordering = ["id"]

    def __str__(self):
        return self.object


# 照片分享表
class PhotoShare(models.Model):
    SHARE_TYPE = (
        (0, '不限制查看'),
        (1, '每个人可查看一次'),
        (2, '仅好友可查看'),
        (3, '仅好友可查看一次')
    )
    id = models.AutoField(primary_key=True, verbose_name="编号")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, verbose_name="照片")
    create_time = models.DateTimeField(auto_created=True, auto_now_add=True, verbose_name="创建时间")
    share_type = models.IntegerField(choices=SHARE_TYPE, default=0, verbose_name="状态")
    password = models.CharField(max_length=191, blank=True, null=True, verbose_name="分享密码")
    token = models.CharField(max_length=191, unique=True, verbose_name="分享Token")
    viewers = models.ManyToManyField(User, related_name='photo_share_user_viewers', verbose_name="查看者")
    remark = models.TextField(verbose_name="备注", null=True, blank=True)

    class Meta:
        verbose_name = "照片分享"
        verbose_name_plural = verbose_name
        ordering = ["id"]

    def __str__(self):
        return str(self.user.id) + ' - ' + str(self.photo.id)

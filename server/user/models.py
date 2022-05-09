from django.db import models


# Create your models here.

# 用户表
class User(models.Model):
    GENDER_STATUE = (
        (1, '男'),
        (0, '女'),
        (-1, '未知')
    )
    STATUE = (
        (1, '可用'),
        (0, '封禁')
    )
    id = models.AutoField(primary_key=True, verbose_name="编号")
    username = models.CharField(max_length=191, verbose_name="用户名", null=True, blank=True)
    openid = models.CharField(max_length=191, unique=True, verbose_name="微信openid")
    avatar = models.CharField(max_length=1191, verbose_name="头像", null=True, blank=True)
    place = models.CharField(max_length=191, verbose_name="地区", null=True, blank=True)
    gender = models.IntegerField(choices=GENDER_STATUE, default=-1, verbose_name="性别", null=True, blank=True)
    register_time = models.DateTimeField(auto_created=True, auto_now_add=True, verbose_name="注册时间")
    status = models.IntegerField(choices=STATUE, default=1, verbose_name='状态')
    remark = models.TextField(verbose_name="备注", null=True, blank=True)

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name
        ordering = ["id"]

    def __str__(self):
        return self.openid


# 用户关系表
class UserRelationship(models.Model):
    TYPE_STATUE = (
        (1, '好友'),
        (-1, '拉黑')
    )
    id = models.AutoField(primary_key=True, verbose_name="编号")
    origin = models.ForeignKey(User, related_name='user_userrelationship_origin', on_delete=models.CASCADE, verbose_name="发起用户")
    target = models.ForeignKey(User, related_name='user_userrelationship_target', on_delete=models.CASCADE, verbose_name="目标用户")
    type = models.IntegerField(choices=TYPE_STATUE, default=-1, verbose_name="关系类型")
    relationship = models.CharField(max_length=191, unique=True, verbose_name="关系Token")
    create_time = models.DateTimeField(auto_created=True, auto_now_add=True, verbose_name="创建时间")
    twoway = models.BooleanField(default=False, verbose_name="双向好友")
    remark = models.TextField(verbose_name="备注", null=True, blank=True)

    class Meta:
        verbose_name = "用户关系"
        verbose_name_plural = verbose_name
        ordering = ["id"]

    def __str__(self):
        return self.relationship
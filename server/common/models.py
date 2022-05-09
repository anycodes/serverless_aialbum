from django.db import models


# Create your models here.


# 标签表
class Tag(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="编号")
    name = models.CharField(max_length=191, verbose_name="标签名")
    remark = models.TextField(verbose_name="备注", null=True, blank=True)

    class Meta:
        verbose_name = "标签"
        verbose_name_plural = verbose_name
        ordering = ["id"]

    def __str__(self):
        return self.name

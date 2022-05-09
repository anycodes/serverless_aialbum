from django.contrib import admin
from photo.models import Photo, PhotoShare


# Register your models here.


class PhotoAdmin(admin.ModelAdmin):
    ordering = ('-id',)
    list_display = ('id', 'upload_user', 'type', 'lifecycle', 'object',)
    list_display_links = ('id', 'upload_user', 'object',)


class PhotoShareAdmin(admin.ModelAdmin):
    ordering = ('-id',)
    list_display = ('id', 'user', 'photo', 'create_time', 'share_type', 'token')
    list_display_links = ('id', 'user', 'photo', 'token',)


admin.site.register(Photo, PhotoAdmin)
admin.site.register(PhotoShare, PhotoShareAdmin)

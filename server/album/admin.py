from django.contrib import admin
from album import Album, UserAlbum


# Register your models here.


class AlbumAdmin(admin.ModelAdmin):
    ordering = ('-id',)
    list_display = ('id', 'name', 'user', 'create_time', 'acl')
    list_display_links = ('id', 'name', 'user',)

class AlbumUserAdmin(admin.ModelAdmin):
    ordering = ('-id',)
    list_display = ('id', 'album', 'user', 'acl_type', 'create_time')
    list_display_links = ('id', 'album', 'user',)


admin.site.register(Album, AlbumAdmin)
admin.site.register(UserAlbum, AlbumUserAdmin)

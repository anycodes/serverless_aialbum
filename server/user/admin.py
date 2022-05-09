from django.contrib import admin
from server.user.models import User, UserRelationship

# Register your models here.


class UserAdmin(admin.ModelAdmin):
    ordering = ('-id',)
    list_display = ('id', 'username', 'place', 'gender', 'register_time', 'status',)
    list_display_links = ('id', 'username',)
    list_editable = ('status',)


class UserRelationshipAdmin(admin.ModelAdmin):
    ordering = ('-id',)
    list_display = ('id', 'origin', 'target', 'type', 'create_time',)
    list_display_links = ('id', 'origin', 'target', 'type', 'create_time',)


admin.site.register(User, UserAdmin)
admin.site.register(UserRelationship, UserRelationshipAdmin)

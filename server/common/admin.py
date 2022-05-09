from django.contrib import admin
from server.common import Tag

# Register your models here.

class TagAdmin(admin.ModelAdmin):
    ordering = ('-id',)
    list_display = ('id', 'name', 'remark')
    list_display_links = ('id', 'name', 'remark')


admin.site.register(Tag, TagAdmin)

from django.contrib import admin
from Journal import models
from django.utils import timezone
from datetime import timedelta

# 注册模型才会在admin界面显示
admin.site.register(models.User)
admin.site.register(models.Photo)
admin.site.register(models.Favorite)
admin.site.register(models.CommentPhoto)

class LocationAdmin(admin.ModelAdmin):
    """地点模型的Admin类"""
    list_display = ['title', 'address', 'user', 'display_created_at']
    
    def display_created_at(self, obj):
        """显示东八区时间"""
        # 将UTC时间转换为东八区时间
        tz_aware_time = timezone.make_aware(obj.created_at, timezone.get_current_timezone())
        # 转换为东八区
        china_time = tz_aware_time + timedelta(hours=8)
        return china_time.strftime('%Y-%m-%d %H:%M:%S')
    
    display_created_at.short_description = '创建时间(东八区)'

class CommentAdmin(admin.ModelAdmin):
    """评论模型的Admin类"""
    list_display = ['content', 'user', 'location', 'display_created_at']
    
    def display_created_at(self, obj):
        """显示东八区时间"""
        # 将UTC时间转换为东八区时间
        tz_aware_time = timezone.make_aware(obj.created_at, timezone.get_current_timezone())
        # 转换为东八区
        china_time = tz_aware_time + timedelta(hours=8)
        return china_time.strftime('%Y-%m-%d %H:%M:%S')
    
    display_created_at.short_description = '创建时间(东八区)'

class LikeAdmin(admin.ModelAdmin):
    """点赞模型的Admin类"""
    list_display = ['user', 'content_type', 'object_id', 'display_created_at']
    
    def display_created_at(self, obj):
        """显示东八区时间"""
        # 将UTC时间转换为东八区时间
        tz_aware_time = timezone.make_aware(obj.created_at, timezone.get_current_timezone())
        # 转换为东八区
        china_time = tz_aware_time + timedelta(hours=8)
        return china_time.strftime('%Y-%m-%d %H:%M:%S')
    
    display_created_at.short_description = '点赞时间(东八区)'

# 注册带自定义Admin类的模型
admin.site.register(models.Location, LocationAdmin)
admin.site.register(models.Comment, CommentAdmin)
admin.site.register(models.Like, LikeAdmin)
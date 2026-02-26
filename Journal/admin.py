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
    list_display = ['title', 'address', 'user', 'created_at', 'display_china_time']
    readonly_fields = ['created_at']
    
    def display_china_time(self, obj):
        """显示东八区时间"""
        try:
            # 检查created_at是否已经是带时区的时间
            if hasattr(obj.created_at, 'tzinfo') and obj.created_at.tzinfo is not None:
                # 已经带时区，直接转换
                china_time = obj.created_at + timedelta(hours=8)
            else:
                # 不带时区，先设置为UTC，再转换
                utc_time = timezone.make_aware(obj.created_at, timezone.utc)
                china_time = utc_time + timedelta(hours=8)
            return china_time.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            return f"错误: {str(e)}"
    
    display_china_time.short_description = '创建时间(东八区)'

class CommentAdmin(admin.ModelAdmin):
    """评论模型的Admin类"""
    list_display = ['content', 'user', 'location', 'created_at', 'display_china_time']
    readonly_fields = ['created_at']
    
    def display_china_time(self, obj):
        """显示东八区时间"""
        try:
            # 检查created_at是否已经是带时区的时间
            if hasattr(obj.created_at, 'tzinfo') and obj.created_at.tzinfo is not None:
                # 已经带时区，直接转换
                china_time = obj.created_at + timedelta(hours=8)
            else:
                # 不带时区，先设置为UTC，再转换
                utc_time = timezone.make_aware(obj.created_at, timezone.utc)
                china_time = utc_time + timedelta(hours=8)
            return china_time.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            return f"错误: {str(e)}"
    
    display_china_time.short_description = '创建时间(东八区)'

class LikeAdmin(admin.ModelAdmin):
    """点赞模型的Admin类"""
    list_display = ['user', 'content_type', 'object_id', 'created_at', 'display_china_time']
    readonly_fields = ['created_at']
    
    def display_china_time(self, obj):
        """显示东八区时间"""
        try:
            # 检查created_at是否已经是带时区的时间
            if hasattr(obj.created_at, 'tzinfo') and obj.created_at.tzinfo is not None:
                # 已经带时区，直接转换
                china_time = obj.created_at + timedelta(hours=8)
            else:
                # 不带时区，先设置为UTC，再转换
                utc_time = timezone.make_aware(obj.created_at, timezone.utc)
                china_time = utc_time + timedelta(hours=8)
            return china_time.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            return f"错误: {str(e)}"
    
    display_china_time.short_description = '点赞时间(东八区)'

# 注册带自定义Admin类的模型
admin.site.register(models.Location, LocationAdmin)
admin.site.register(models.Comment, CommentAdmin)
admin.site.register(models.Like, LikeAdmin)
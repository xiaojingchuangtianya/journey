from django.contrib import admin
from Journal import models
from django.utils import timezone
from datetime import timedelta

class UserAdmin(admin.ModelAdmin):
    """用户模型的Admin类"""
    list_display = ['username', 'nickname', 'display_china_time']
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
    
    display_china_time.short_description = '创建时间'

class LocationAdmin(admin.ModelAdmin):
    """地点模型的Admin类"""
    list_display = ['title', 'address', 'user', 'display_china_time']
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
    
    display_china_time.short_description = '创建时间'

class CommentAdmin(admin.ModelAdmin):
    """评论模型的Admin类"""
    list_display = ['content', 'user', 'location', 'display_china_time']
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
    
    display_china_time.short_description = '创建时间'

class LikeAdmin(admin.ModelAdmin):
    """点赞模型的Admin类"""
    list_display = ['user', 'content_type', 'object_id', 'display_china_time']
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
    
    display_china_time.short_description = '点赞时间'

class FavoriteAdmin(admin.ModelAdmin):
    """收藏模型的Admin类"""
    list_display = ['user', 'location', 'display_china_time']
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
    
    display_china_time.short_description = '收藏时间'

class CommentPhotoAdmin(admin.ModelAdmin):
    """评论照片模型的Admin类"""
    list_display = ['comment', 'display_china_time']
    readonly_fields = ['uploaded_at']
    
    def display_china_time(self, obj):
        """显示东八区时间"""
        try:
            # 检查uploaded_at是否已经是带时区的时间
            if hasattr(obj.uploaded_at, 'tzinfo') and obj.uploaded_at.tzinfo is not None:
                # 已经带时区，直接转换
                china_time = obj.uploaded_at + timedelta(hours=8)
            else:
                # 不带时区，先设置为UTC，再转换
                utc_time = timezone.make_aware(obj.uploaded_at, timezone.utc)
                china_time = utc_time + timedelta(hours=8)
            return china_time.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            return f"错误: {str(e)}"
    
    display_china_time.short_description = '上传时间'

class PhotoAdmin(admin.ModelAdmin):
    """照片模型的Admin类"""
    list_display = ['location', 'is_main', 'display_china_time']
    readonly_fields = ['uploaded_at']
    
    def display_china_time(self, obj):
        """显示东八区时间"""
        try:
            # 检查uploaded_at是否已经是带时区的时间
            if hasattr(obj.uploaded_at, 'tzinfo') and obj.uploaded_at.tzinfo is not None:
                # 已经带时区，直接转换
                china_time = obj.uploaded_at + timedelta(hours=8)
            else:
                # 不带时区，先设置为UTC，再转换
                utc_time = timezone.make_aware(obj.uploaded_at, timezone.utc)
                china_time = utc_time + timedelta(hours=8)
            return china_time.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            return f"错误: {str(e)}"
    
    display_china_time.short_description = '上传时间'

# 注册带自定义Admin类的模型
admin.site.register(models.User, UserAdmin)
admin.site.register(models.Location, LocationAdmin)
admin.site.register(models.Comment, CommentAdmin)
admin.site.register(models.Like, LikeAdmin)
admin.site.register(models.Photo, PhotoAdmin)
admin.site.register(models.Favorite, FavoriteAdmin)
admin.site.register(models.CommentPhoto, CommentPhotoAdmin)
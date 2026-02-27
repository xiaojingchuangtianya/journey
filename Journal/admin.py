from django.contrib import admin
from Journal import models
from django.utils import timezone

class BaseAdmin(admin.ModelAdmin):
    """基础Admin类，包含通用功能"""
    list_per_page = 20  # 每页显示20条记录
    ordering = ['-created_at']  # 默认按创建时间倒序排列

class UserAdmin(BaseAdmin):
    """用户模型的Admin类"""
    list_display = ['username', 'nickname', 'gender', 'isGetAvatar', 'isGetNickname', 'created_at']
    search_fields = ['username', 'nickname']  # 搜索字段
    list_filter = ['gender', 'isGetAvatar', 'isGetNickname']  # 过滤字段
    readonly_fields = ['created_at']

class LocationAdmin(BaseAdmin):
    """地点模型的Admin类"""
    list_display = ['title', 'address', 'user', 'created_at']
    search_fields = ['title', 'address']  # 搜索字段
    list_filter = ['user']  # 过滤字段
    readonly_fields = ['created_at']

class CommentAdmin(BaseAdmin):
    """评论模型的Admin类"""
    list_display = ['content', 'user', 'location', 'created_at']
    search_fields = ['content']  # 搜索字段
    list_filter = ['user', 'location']  # 过滤字段
    readonly_fields = ['created_at']

class LikeAdmin(BaseAdmin):
    """点赞模型的Admin类"""
    list_display = ['user', 'content_type', 'object_id', 'created_at']
    list_filter = ['user', 'content_type']  # 过滤字段
    readonly_fields = ['created_at']

class FavoriteAdmin(BaseAdmin):
    """收藏模型的Admin类"""
    list_display = ['user', 'location', 'created_at']
    list_filter = ['user', 'location']  # 过滤字段
    readonly_fields = ['created_at']

class CommentPhotoAdmin(BaseAdmin):
    """评论照片模型的Admin类"""
    list_display = ['comment', 'uploaded_at']
    list_filter = ['comment']  # 过滤字段
    readonly_fields = ['uploaded_at']
    ordering = ['-uploaded_at']  # 按上传时间倒序排列

class PhotoAdmin(BaseAdmin):
    """照片模型的Admin类"""
    list_display = ['location', 'is_main', 'uploaded_at']
    list_filter = ['location', 'is_main']  # 过滤字段
    readonly_fields = ['uploaded_at']
    ordering = ['-uploaded_at']  # 按上传时间倒序排列

# 注册带自定义Admin类的模型
admin.site.register(models.User, UserAdmin)
admin.site.register(models.Location, LocationAdmin)
admin.site.register(models.Comment, CommentAdmin)
admin.site.register(models.Like, LikeAdmin)
admin.site.register(models.Photo, PhotoAdmin)
admin.site.register(models.Favorite, FavoriteAdmin)
admin.site.register(models.CommentPhoto, CommentPhotoAdmin)

# 修改admin站点标题
admin.site.site_header = '露营地管理系统'
admin.site.site_title = '露营地管理系统'
admin.site.index_title = '欢迎使用露营地管理系统'
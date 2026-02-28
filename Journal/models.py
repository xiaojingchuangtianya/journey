from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class UserManager(BaseUserManager):
    def create_user(self, username, email=None, **extra_fields):
        if not username:
            raise ValueError('用户必须有用户名')
        user = self.model(username=username, **extra_fields)
        user.save(using=self._db)
        return user
    
class CommentManager(BaseUserManager):
    def create_comment(self, is_parent, parent):
        if is_parent:
            parent = None
        comment = self.model(is_parent=is_parent, parent=parent)
        comment.save(using=self._db)
        return comment




class User(AbstractBaseUser):
    # 性别选择
    GENDER_CHOICES = (
        ('M', '男'),
        ('F', '女'),
        ('O', '其他'),
    )
    isGetAvatar = models.BooleanField(default=False, verbose_name='是否获取上传头像',null=True, blank=True)
    isGetNickname = models.BooleanField(default=False, verbose_name='是否获取用户名',null=True, blank=True)
    # 基本信息
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='头像')
    username = models.CharField(max_length=100, unique=True, verbose_name='用户名')

    nickname = models.CharField(max_length=100, verbose_name='名称')
    # 用户性别
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True, verbose_name='性别')
    # IP归属信息
    ip_location = models.CharField(max_length=200, null=True, blank=True, verbose_name='IP归属')
    # 头像

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    # 设置用户管理器
    objects = UserManager()
    # 设置登录字段
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['nickname']
    class Meta:
        app_label = 'Journal'
        verbose_name = '用户'
        verbose_name_plural = '用户'
    def __str__(self):
        return self.nickname or self.username


class Location(models.Model):
    """地点模型"""
    # 标题
    title = models.CharField(max_length=200, verbose_name='标题')
    # 内容，得支持图片
    content = models.TextField(verbose_name='内容')
    # 时间（创建时间）
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    # 区域
    region = models.CharField(max_length=100, null=True, blank=True, verbose_name='区域')
    # 是否免费
    is_free = models.BooleanField(null=True, blank=True, verbose_name='是否免费')
    # 地址
    address = models.CharField(max_length=300, verbose_name='地址')
    # 经度
    longitude = models.FloatField(null=True, blank=True, verbose_name='经度')
    # 纬度
    latitude = models.FloatField(null=True, blank=True, verbose_name='纬度')
    # 分享用户（关联到User）
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locations', verbose_name='分享用户')   
    # 置顶评论（与Comment的一对一关系）
    featured_comment = models.OneToOneField(
        'Comment', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='featured_in_location', 
        verbose_name='置顶评论'
    )
    
    class Meta:
        app_label = 'Journal'
        verbose_name = '地点'
        verbose_name_plural = '地点'
        ordering = ['-created_at']  # 按创建时间降序排列
    
    def __str__(self):
        return f'{self.title} - {self.address}'


class Comment(models.Model):
    """评论模型"""
    # 评论内容
    content = models.TextField(verbose_name='评论内容')
    # 是否父级评论
    is_parent = models.BooleanField(default=True, verbose_name='是否父级评论')
    # 关联父级评论id（自关联）
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies', verbose_name='父级评论')

    # 关联到用户
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', verbose_name='评论用户')
    # 关联到地点
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='comments', verbose_name='关联地点',null=True,blank=True)
    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    # 增加一个评论触发器检查
    objects = CommentManager()
    class Meta:
        app_label = 'Journal'
        verbose_name = '评论'
        verbose_name_plural = '评论'
        ordering = ['-created_at']  # 按创建时间降序排列
    
    def __str__(self):
        return f'{self.content} by {self.user.nickname} at {self.created_at}'


class Photo(models.Model):
    """照片模型，用于存储地点的多张照片"""
    # 关联到地点
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='photos', verbose_name='关联地点', null=True, blank=True)
    # 照片文件
    image = models.ImageField(upload_to='location_photos/', verbose_name='照片')
    # 上传时间
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    # 是否主图
    is_main = models.BooleanField(default=False, verbose_name='是否主图')
    
    class Meta:
        app_label = 'Journal'
        verbose_name = '照片'
        verbose_name_plural = '照片'
        ordering = ['-is_main', 'uploaded_at']  # 主图排在前面，然后按上传时间排序
    
    def __str__(self):
        return f'照片 for {self.location.title} - {self.id}'


class CommentPhoto(models.Model):
    """评论照片模型，用于存储评论的多张照片"""
    # 关联到评论
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='photos', verbose_name='关联评论')
    # 照片文件
    image = models.ImageField(upload_to='comment_photos/', verbose_name='照片')
    # 上传时间
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    
    class Meta:
        app_label = 'Journal'
        verbose_name = '评论照片'
        verbose_name_plural = '评论照片'
        ordering = ['uploaded_at']  # 按上传时间排序
    
    def __str__(self):
        return f'评论照片 for {self.comment.content[:20]}... - {self.id}'


class Like(models.Model):
    """点赞模型，支持对不同类型对象的点赞"""
    # 点赞用户
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='likes', verbose_name='点赞用户')
    # 关联内容类型
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name='内容类型')
    # 关联对象ID
    object_id = models.PositiveIntegerField(verbose_name='对象ID')
    # 通用外键，关联到具体对象
    content_object = GenericForeignKey('content_type', 'object_id')
    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='点赞时间')
    
    class Meta:
        app_label = 'Journal'
        verbose_name = '点赞'
        verbose_name_plural = '点赞'
        ordering = ['-created_at']  # 按点赞时间降序排列
    
    def __str__(self):
        return f'{self.user.nickname if self.user else "未知用户"} 点赞了 {self.content_type.model} {self.object_id}'


class Favorite(models.Model):
    """收藏模型，记录用户收藏的地点"""
    # 收藏用户
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name='收藏用户')
    # 关联地点
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='favorites', verbose_name='收藏地点')
    # 收藏时间
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='收藏时间')
    
    class Meta:
        app_label = 'Journal'
        verbose_name = '收藏'
        verbose_name_plural = '收藏'
        # 确保每个用户对每个地点只能收藏一次
        unique_together = ('user', 'location')
        ordering = ['-created_at']  # 按收藏时间降序排列
    
    def __str__(self):
        return f'{self.user.nickname} 收藏了 {self.location.title}'








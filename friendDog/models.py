from django.db import models
from django.contrib.auth.models import User

class DogProfile(models.Model):
    """小狗资料模型"""
    # 基本信息
    nickname = models.CharField(max_length=100, verbose_name='昵称')
    breed = models.CharField(max_length=100, verbose_name='品种')
    # 出生日期
    birth_date = models.DateField(verbose_name='出生日期')
    
    # 性别选择
    GENDER_CHOICES = (
        ('M', '公'),
        ('F', '母'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name='性别')
    
    # 婚育情况
    MARITAL_STATUS_CHOICES = (
        ('S', '单身'),
        ('M', '已配对'),
        ('P', '已生育'),
    )
    marital_status = models.CharField(max_length=1, choices=MARITAL_STATUS_CHOICES, verbose_name='婚育情况')
    
    # 小狗简介
    bio = models.TextField(verbose_name='小狗简介', blank=True, null=True)
    
    # IP地市
    location = models.CharField(max_length=100, verbose_name='所在地市')
    
    # MBTI性格类型
    MBTI_CHOICES = (
        ('ISTJ', 'ISTJ'),
        ('ISFJ', 'ISFJ'),
        ('INFJ', 'INFJ'),
        ('INTJ', 'INTJ'),
        ('ISTP', 'ISTP'),
        ('ISFP', 'ISFP'),
        ('INFP', 'INFP'),
        ('INTP', 'INTP'),
        ('ESTP', 'ESTP'),
        ('ESFP', 'ESFP'),
        ('ENFP', 'ENFP'),
        ('ENTP', 'ENTP'),
        ('ESTJ', 'ESTJ'),
        ('ESFJ', 'ESFJ'),
        ('ENFJ', 'ENFJ'),
        ('ENTJ', 'ENTJ'),
    )
    mbti = models.CharField(max_length=4, choices=MBTI_CHOICES, blank=True, null=True, verbose_name='MBTI性格类型')
    
    # 主人信息（关联到User）
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dog_profiles', verbose_name='主人')
    
    # 注册时间
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='注册时间')
    # 更新时间
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        app_label = 'friendDog'
        verbose_name = '小狗资料'
        verbose_name_plural = '小狗资料'
        ordering = ['-created_at']  # 按注册时间降序排列
    
    def __str__(self):
        return f'{self.nickname} ({self.breed})'


class DogAvatar(models.Model):
    """小狗头像模型"""
    # 关联到小狗资料
    dog_profile = models.OneToOneField(DogProfile, on_delete=models.CASCADE, related_name='avatar', verbose_name='关联小狗资料')
    # 头像图片
    image = models.ImageField(upload_to='dog_avatars/', verbose_name='头像图片')
    # 上传时间
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    
    class Meta:
        app_label = 'friendDog'
        verbose_name = '小狗头像'
        verbose_name_plural = '小狗头像'
    
    def __str__(self):
        return f'头像 for {self.dog_profile.nickname}'


class DogWalkRecord(models.Model):
    """遛狗记录模型"""
    # 关联到用户
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='walk_records', verbose_name='记录用户')
    # 关联到小狗资料
    dog_profile = models.ForeignKey(DogProfile, on_delete=models.CASCADE, related_name='walk_records', verbose_name='关联小狗')
    
    # 开始时间
    start_time = models.DateTimeField(verbose_name='开始时间')
    # 结束时间
    end_time = models.DateTimeField(verbose_name='结束时间')
    # 地点
    location = models.CharField(max_length=200, verbose_name='遛狗地点')
    # 距离（单位：米）
    distance = models.FloatField(verbose_name='距离(米)')
    
    # 天气选择
    WEATHER_CHOICES = (
        ('SUNNY', '晴天'),
        ('CLOUDY', '多云'),
        ('RAINY', '雨天'),
        ('SNOWY', '雪天'),
        ('WINDY', '大风'),
        ('FOGGY', '雾天'),
    )
    weather = models.CharField(max_length=10, choices=WEATHER_CHOICES, verbose_name='天气')
    
    mood = models.CharField(max_length=50, blank=True, null=True, verbose_name='心情')
    
    # 注册时间
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    # 编辑时间
    updated_at = models.DateTimeField(auto_now=True, verbose_name='编辑时间')
    
    class Meta:
        app_label = 'friendDog'
        verbose_name = '遛狗记录'
        verbose_name_plural = '遛狗记录'
        ordering = ['-created_at']  # 按创建时间降序排列
    
    def __str__(self):
        return f'{self.dog_profile.nickname} - {self.start_time.strftime("%Y-%m-%d %H:%M")}'


class DogWalkPhoto(models.Model):
    """遛狗照片模型，支持多张照片"""
    # 关联到遛狗记录
    walk_record = models.ForeignKey(DogWalkRecord, on_delete=models.CASCADE, related_name='photos', verbose_name='关联遛狗记录')
    # 照片文件
    image = models.ImageField(upload_to='walk_photos/', verbose_name='遛狗图片')
    # 上传时间
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    
    class Meta:
        app_label = 'friendDog'
        verbose_name = '遛狗照片'
        verbose_name_plural = '遛狗照片'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f'遛狗照片 for {self.walk_record.dog_profile.nickname} - {self.id}'


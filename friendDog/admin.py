from django.contrib import admin
from .models import DogProfile, DogAvatar, DogWalkRecord, DogWalkPhoto

# 注册小狗资料模型
@admin.register(DogProfile)
class DogProfileAdmin(admin.ModelAdmin):
    list_display = ('nickname', 'breed', 'gender', 'owner', 'created_at')
    search_fields = ('nickname', 'breed', 'owner__username')
    list_filter = ('gender', 'breed', 'created_at')
    date_hierarchy = 'created_at'

# 注册小狗头像模型
@admin.register(DogAvatar)
class DogAvatarAdmin(admin.ModelAdmin):
    list_display = ('dog_profile', 'uploaded_at')
    search_fields = ('dog_profile__nickname',)
    list_filter = ('uploaded_at',)

# 注册遛狗记录模型
@admin.register(DogWalkRecord)
class DogWalkRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'dog_profile', 'start_time', 'end_time', 'location', 'weather', 'mood')
    search_fields = ('user__username', 'dog_profile__nickname', 'location')
    list_filter = ('weather', 'mood', 'created_at')
    date_hierarchy = 'start_time'

# 注册遛狗照片模型
@admin.register(DogWalkPhoto)
class DogWalkPhotoAdmin(admin.ModelAdmin):
    list_display = ('walk_record', 'uploaded_at')
    search_fields = ('walk_record__dog_profile__nickname',)
    list_filter = ('uploaded_at',)

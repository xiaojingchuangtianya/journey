from django.contrib import admin
from Journal import models

# Register your models here.
# 需要注册模型才会在admin界面显示
admin.site.register(models.User)
admin.site.register(models.Location)
admin.site.register(models.Comment)
admin.site.register(models.Like)
admin.site.register(models.Photo)

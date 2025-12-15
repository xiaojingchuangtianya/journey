#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查生成的数据量
"""

import os
import sys

# 添加Django项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Journey.settings')

# 导入Django
import django
django.setup()

# 导入模型
from Journal.models import User, Location, Comment, Photo, Like


def check_data_count():
    """检查数据库中的数据量"""
    print("数据库数据统计:")
    print(f"用户数量: {User.objects.count()}")
    print(f"地点数量: {Location.objects.count()}")
    print(f"评论数量: {Comment.objects.count()}")
    print(f"照片数量: {Photo.objects.count()}")
    print(f"点赞数量: {Like.objects.count()}")
    
    total = User.objects.count() + Location.objects.count() + Comment.objects.count() + Photo.objects.count() + Like.objects.count()
    print(f"\n总数据量: {total}")


if __name__ == '__main__':
    check_data_count()

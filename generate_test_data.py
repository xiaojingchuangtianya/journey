#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成测试数据脚本
生成100条数据到Journal应用的数据库中
"""

import os
import sys
import random
import string
from datetime import datetime, timedelta

# 添加Django项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Journey.settings')

# 导入Django
import django
django.setup()

# 导入模型
from Journal.models import User, Location, Comment, Photo, Like
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
import io
from PIL import Image


def generate_random_string(length=10):
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_Chinese_string(length=5):
    """生成随机中文字符串"""
    # 简单的中文字符集，实际使用时可以扩展
    Chinese_chars = '一二三四五六七八九十甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥'
    return ''.join(random.choices(Chinese_chars, k=length))


def create_dummy_image():
    """创建一个虚拟的图片文件"""
    # 创建一个1x1的红色图片
    image = Image.new('RGB', (1, 1), color='red')
    # 将图片保存到内存中
    image_io = io.BytesIO()
    image.save(image_io, format='JPEG')
    image_io.seek(0)
    # 创建一个Django文件对象
    return File(image_io, name=f'dummy_image_{generate_random_string()}.jpg')


def generate_test_data():
    """生成测试数据"""
    print("开始生成测试数据...")
    
    # 生成用户数据
    users = []
    for i in range(10):  # 创建10个用户
        username = f'user_{generate_random_string(6)}'
        nickname = f'{generate_random_Chinese_string(3)}用户{i+1}'
        gender = random.choice(['M', 'F', 'O'])
        ip_location = f'城市{generate_random_Chinese_string(2)}'
        
        # 创建用户
        user = User.objects.create(
            username=username,
            nickname=nickname,
            gender=gender,
            ip_location=ip_location
        )
        users.append(user)
        print(f"创建用户: {user.nickname}")
    
    # 生成地点数据
    locations = []
    for i in range(20):  # 创建20个地点
        title = f'{generate_random_Chinese_string(4)}露营地'
        content = f'这是一个美丽的露营地，环境优美，适合户外休闲。{generate_random_Chinese_string(20)}'
        address = f'{generate_random_Chinese_string(3)}省{generate_random_Chinese_string(2)}市{generate_random_Chinese_string(3)}区'
        user = random.choice(users)
        
        # 创建地点
        location = Location.objects.create(
            title=title,
            content=content,
            address=address,
            user=user
        )
        
        # 为地点添加照片
        photo_count = random.randint(1, 5)
        for j in range(photo_count):
            try:
                Photo.objects.create(
                    location=location,
                    # 在实际运行时，我们可能需要真实的图片文件
                    # 这里为了演示，我们跳过图片上传
                    # image=create_dummy_image(),
                    is_main=(j == 0)  # 第一张设为主图
                )
            except Exception as e:
                print(f"创建照片失败: {e}")
        
        locations.append(location)
        print(f"创建地点: {location.title}")
    
    # 生成评论数据
    comments = []
    for i in range(50):  # 创建50条评论
        content = f'这是一条评论内容。{generate_random_Chinese_string(10)}'
        user = random.choice(users)
        location = random.choice(locations)
        
        # 决定是否是父级评论
        is_parent = random.random() > 0.3  # 70%的概率是父级评论
        
        if is_parent or not comments:
            # 创建父级评论
            comment = Comment.objects.create(
                content=content,
                is_parent=True,
                parent=None,
                user=user,
                location=location
            )
        else:
            # 创建回复评论
            parent = random.choice([c for c in comments if c.is_parent])
            comment = Comment.objects.create(
                content=content,
                is_parent=False,
                parent=parent,
                user=user,
                location=location
            )
        
        comments.append(comment)
        print(f"创建评论: {comment.content[:20]}...")
    
    # 为一些地点设置置顶评论
    for location in locations:
        location_comments = [c for c in comments if c.location == location and c.is_parent]
        if location_comments:
            featured_comment = random.choice(location_comments)
            location.featured_comment = featured_comment
            location.save()
    
    # 生成点赞数据
    for i in range(100):  # 创建100个点赞
        user = random.choice(users)
        
        # 随机选择点赞对象类型
        target_type = random.choice(['location', 'comment'])
        
        if target_type == 'location':
            target = random.choice(locations)
            content_type = ContentType.objects.get_for_model(Location)
        else:
            target = random.choice(comments)
            content_type = ContentType.objects.get_for_model(Comment)
        
        # 避免重复点赞
        try:
            like, created = Like.objects.get_or_create(
                user=user,
                content_type=content_type,
                object_id=target.id
            )
            if created:
                print(f"创建点赞: 用户{user.nickname} 点赞了 {target_type} {target.id}")
        except Exception as e:
            print(f"创建点赞失败: {e}")
    
    print("测试数据生成完成！")
    print(f"创建了 {len(users)} 个用户")
    print(f"创建了 {len(locations)} 个地点")
    print(f"创建了 {len(comments)} 条评论")
    print(f"创建了 {Like.objects.count()} 个点赞")


if __name__ == '__main__':
    try:
        generate_test_data()
    except Exception as e:
        print(f"生成数据时出错: {e}")
        import traceback
        traceback.print_exc()

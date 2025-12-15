#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
脚本功能：将Photo模型中id=1的图片复制到其他所有Photo记录中
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Journey.settings')
django.setup()

from Journal.models import Photo
from django.core.files.base import ContentFile
import uuid
import glob

def copy_photo_to_all():
    """将id=1的图片复制到其他所有Photo记录"""
    try:
        # 获取id=1的Photo记录
        source_photo = Photo.objects.get(id=1)
        print(f"找到源图片: ID={source_photo.id}, 图片路径={source_photo.image.path}")
        print(f"图片名称: {source_photo.image.name}")
        
        # 查找实际的图片文件
        image_filename = os.path.basename(source_photo.image.name)
        print(f"尝试查找文件名: {image_filename}")
        
        # 搜索location_photos目录下的所有子目录
        search_pattern = os.path.join('location_photos', '**', image_filename)
        found_files = glob.glob(search_pattern, recursive=True)
        
        if not found_files:
            # 如果找不到，尝试搜索location_photos根目录
            root_pattern = os.path.join('location_photos', image_filename)
            found_files = glob.glob(root_pattern)
        
        if found_files:
            actual_image_path = found_files[0]
            print(f"找到实际图片文件: {actual_image_path}")
            
            # 读取源图片内容
            with open(actual_image_path, 'rb') as f:
                image_content = f.read()
            
            # 获取其他所有Photo记录（排除id=1）
            other_photos = Photo.objects.exclude(id=1)
            total = other_photos.count()
            print(f"找到 {total} 条需要更新的图片记录")
            
            updated_count = 0
            # 更新其他记录
            for photo in other_photos:
                try:
                    # 生成新的文件名，保持原扩展名
                    ext = os.path.splitext(image_filename)[1]
                    new_filename = f"{uuid.uuid4().hex}{ext}"
                    
                    # 设置新的图片内容
                    photo.image.save(new_filename, ContentFile(image_content), save=True)
                    updated_count += 1
                    print(f"已更新图片 ID={photo.id}")
                except Exception as e:
                    print(f"更新图片 ID={photo.id} 时出错: {str(e)}")
            
            print(f"\n更新完成！成功更新 {updated_count}/{total} 条记录")
        else:
            print(f"错误: 在location_photos目录下找不到文件: {image_filename}")
            # 尝试列出目录内容
            print("\nlocation_photos目录内容:")
            if os.path.exists('location_photos'):
                for root, dirs, files in os.walk('location_photos'):
                    level = root.replace('location_photos', '').count(os.sep)
                    indent = ' ' * 4 * level
                    print(f"{indent}{os.path.basename(root)}/")
                    subindent = ' ' * 4 * (level + 1)
                    for file in files:
                        print(f"{subindent}{file}")
        
    except Photo.DoesNotExist:
        print("错误: 找不到id=1的Photo记录")
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    print("开始执行图片复制操作...")
    copy_photo_to_all()
    print("操作完成！")

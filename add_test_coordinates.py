#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为现有地点添加测试经纬度数据
"""

import os
import sys
import random

# 添加Django项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Journey.settings')

# 导入Django并初始化
import django
django.setup()

# 导入模型
from Journal.models import Location


def add_test_coordinates():
    """
    为所有没有经纬度的地点随机生成测试经纬度数据
    使用北京地区的大致坐标范围
    """
    print("开始为地点添加测试经纬度数据...")
    
    # 获取所有没有经纬度的地点
    locations_without_coords = Location.objects.filter(
        longitude__isnull=True, latitude__isnull=True
    )
    
    total = locations_without_coords.count()
    print(f"找到 {total} 个没有经纬度数据的地点")
    
    if total == 0:
        print("所有地点都已有经纬度数据！")
        return
    
    updated_count = 0
    
    # 北京地区大致坐标范围
    beijing_lon_range = (116.0, 116.8)  # 经度范围
    beijing_lat_range = (39.6, 40.2)    # 纬度范围
    
    # 为每个地点生成随机经纬度
    for location in locations_without_coords:
        try:
            # 生成随机经纬度
            longitude = round(random.uniform(*beijing_lon_range), 6)
            latitude = round(random.uniform(*beijing_lat_range), 6)
            
            # 更新地点
            location.longitude = longitude
            location.latitude = latitude
            location.save()
            
            updated_count += 1
            print(f"✅ 已更新 {location.title}: 经度={longitude}, 纬度={latitude}")
            
        except Exception as e:
            print(f"❌ 更新 {location.title} 失败: {str(e)}")
    
    print(f"\n完成！成功更新 {updated_count}/{total} 个地点")


def show_locations_with_coords():
    """
    显示所有有经纬度数据的地点
    """
    print("\n显示所有有经纬度数据的地点：")
    
    locations_with_coords = Location.objects.filter(
        longitude__isnull=False, latitude__isnull=False
    )
    
    count = locations_with_coords.count()
    print(f"\n共有 {count} 个地点有经纬度数据")
    
    if count > 0:
        print("\n经纬度数据列表：")
        for location in locations_with_coords:
            print(f"- {location.id}: {location.title} (经度: {location.longitude}, 纬度: {location.latitude})")


def update_specific_location(location_id, longitude, latitude):
    """
    更新指定地点的经纬度
    """
    try:
        location = Location.objects.get(id=location_id)
        location.longitude = longitude
        location.latitude = latitude
        location.save()
        print(f"✅ 已更新地点 ID {location_id} ({location.title}) 的经纬度")
        return True
    except Location.DoesNotExist:
        print(f"❌ 地点 ID {location_id} 不存在")
        return False
    except Exception as e:
        print(f"❌ 更新地点 ID {location_id} 失败: {str(e)}")
        return False


if __name__ == '__main__':
    print("=" * 80)
    print("          地点经纬度测试数据生成工具")
    print("=" * 80)
    print("功能: 为没有经纬度数据的地点添加随机测试坐标")
    print("      使用北京地区的坐标范围")
    print("=" * 80)
    
    # 先显示当前有经纬度的地点
    show_locations_with_coords()
    
    # 添加测试经纬度数据
    add_test_coordinates()
    
    # 再次显示更新后的结果
    show_locations_with_coords()
    
    print("\n" + "=" * 80)
    print("测试经纬度数据添加完成！")
    print("现在您可以运行测试脚本来验证附近地点查询功能")
    print("使用命令: python test_nearby_locations.py")
    print("=" * 80)

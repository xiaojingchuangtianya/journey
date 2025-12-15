#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试根据坐标查询附近地点的API功能
"""

import requests
import json

# 本地测试URL
BASE_URL = 'http://localhost:8000'
API_ENDPOINT = '/api/nearby-locations/'


def test_nearby_locations_api(longitude=116.404, latitude=39.915, radius=5000):
    """
    测试附近地点API
    
    Args:
        longitude (float): 经度
        latitude (float): 纬度
        radius (float): 搜索半径（米）
    """
    print(f"\n测试根据坐标查询附近地点 (经度={longitude}, 纬度={latitude}, 半径={radius}米)...")
    
    try:
        # 构建请求URL和参数
        url = f"{BASE_URL}{API_ENDPOINT}"
        params = {
            'longitude': longitude,
            'latitude': latitude,
            'radius': radius
        }
        
        print(f"请求URL: {url}")
        print(f"请求参数: {params}")
        
        # 发送GET请求
        response = requests.get(url, params=params, timeout=10)
        
        # 检查响应状态码
        print(f"响应状态码: {response.status_code}")
        
        # 解析JSON响应
        result = response.json()
        
        # 打印响应内容（格式化）
        print(f"响应结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 分析结果
        if result.get('status') == 'success':
            print(f"\n✅ 测试成功！")
            print(f"找到 {len(result.get('data', []))} 个附近地点")
            
            # 打印每个地点的信息
            for location in result.get('data', []):
                print(f"- {location.get('title')} (距离: {location.get('distance')}米)")
        else:
            print(f"\n❌ 测试失败！")
            print(f"错误信息: {result.get('message')}")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 连接失败！请确保Django服务器正在运行")
        print(f"提示: 请先运行 'python manage.py runserver' 启动服务器")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")


def test_invalid_parameters():
    """
    测试无效参数的情况
    """
    print(f"\n\n测试无效参数...")
    
    # 测试无效的经度
    print(f"\n测试无效经度:")
    test_nearby_locations_api(longitude=200, latitude=39.915)
    
    # 测试无效的纬度
    print(f"\n测试无效纬度:")
    test_nearby_locations_api(longitude=116.404, latitude=100)
    
    # 测试非数字参数
    print(f"\n测试非数字参数:")
    try:
        url = f"{BASE_URL}{API_ENDPOINT}"
        params = {'longitude': 'abc', 'latitude': 'def'}
        response = requests.get(url, params=params, timeout=10)
        result = response.json()
        print(f"响应状态码: {response.status_code}")
        print(f"响应结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"错误: {str(e)}")


if __name__ == '__main__':
    print("=" * 80)
    print("          根据坐标查询附近地点API测试工具")
    print("=" * 80)
    print("功能说明: 测试根据经纬度坐标和搜索半径查询附近地点的API")
    print("使用方法: 请确保Django服务器正在运行后再执行此脚本")
    print("=" * 80)
    
    # 测试默认坐标（北京天安门附近）
    test_nearby_locations_api()
    
    # 测试不同半径
    test_nearby_locations_api(longitude=116.404, latitude=39.915, radius=10000)  # 10公里
    
    # 测试无效参数
    test_invalid_parameters()
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("注意: 如果连接失败，请确保Django开发服务器正在运行")
    print("使用命令: python manage.py runserver")
    print("=" * 80)

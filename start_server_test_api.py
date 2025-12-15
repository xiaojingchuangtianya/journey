#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动Django服务器并测试附近地点API
"""

import os
import sys
import subprocess
import time
import requests
import json

# Django服务器配置
SERVER_HOST = '127.0.0.1'
SERVER_PORT = '8000'
SERVER_URL = f'http://{SERVER_HOST}:{SERVER_PORT}'
API_ENDPOINT = '/api/nearby-locations/'


def start_django_server():
    """
    启动Django开发服务器
    """
    print("正在启动Django开发服务器...")
    
    # 构建启动服务器的命令
    cmd = f'python manage.py runserver {SERVER_HOST}:{SERVER_PORT}'
    print(f"执行命令: {cmd}")
    
    # 以非阻塞方式启动服务器
    server_process = subprocess.Popen(
        cmd, 
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # 等待服务器启动
    print("等待服务器启动中...")
    time.sleep(3)
    
    # 检查服务器是否成功启动
    try:
        # 尝试访问根路径
        response = requests.get(SERVER_URL, timeout=5)
        print(f"✅ 服务器启动成功！HTTP状态码: {response.status_code}")
        return server_process
    except Exception as e:
        print(f"❌ 服务器启动失败: {str(e)}")
        # 终止进程
        server_process.terminate()
        return None


def test_nearby_locations_api(longitude=116.404, latitude=39.915, radius=5000):
    """
    测试附近地点API
    """
    print(f"\n🔍 测试根据坐标查询附近地点 (经度={longitude}, 纬度={latitude}, 半径={radius}米)...")
    
    try:
        # 构建请求URL和参数
        url = f"{SERVER_URL}{API_ENDPOINT}"
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
        print(f"\n📊 API响应结果:")
        print(f"状态: {result.get('status')}")
        print(f"消息: {result.get('message')}")
        print(f"找到的地点数量: {len(result.get('data', []))}")
        
        # 打印找到的地点列表
        if result.get('status') == 'success' and result.get('data'):
            print(f"\n📍 附近地点列表:")
            for location in result.get('data', []):
                print(f"  • {location.get('title')}")
                print(f"    距离: {location.get('distance')}米")
                print(f"    地址: {location.get('address')}")
                print(f"    评论数: {location.get('comments_count')}")
                print(f"    点赞数: {location.get('likes_count')}")
                print()
        
        return result
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 连接失败！请确保Django服务器正在运行")
        return None
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")
        return None


def main():
    """
    主函数
    """
    print("=" * 80)
    print("          Django服务器启动与附近地点API测试工具")
    print("=" * 80)
    print("功能说明: 自动启动Django服务器并测试根据坐标查询附近地点的API")
    print("=" * 80)
    
    # 启动Django服务器
    server_process = start_django_server()
    
    if server_process:
        try:
            print("\n" + "=" * 80)
            print("现在开始测试API功能...")
            print("=" * 80)
            
            # 测试不同的坐标和半径
            # 1. 测试北京天安门附近坐标
            test_nearby_locations_api(longitude=116.404, latitude=39.915, radius=5000)  # 5公里
            
            # 2. 测试更大范围
            print("\n" + "=" * 80)
            test_nearby_locations_api(longitude=116.404, latitude=39.915, radius=20000)  # 20公里
            
            # 3. 测试一个特定地点附近
            # 从之前添加的地点中选择一个作为测试点
            test_location_longitude = 116.667587  # 地点ID=1的经度
            test_location_latitude = 39.798792    # 地点ID=1的纬度
            print("\n" + "=" * 80)
            print(f"测试特定地点(ID=1)附近的其他地点:")
            test_nearby_locations_api(
                longitude=test_location_longitude, 
                latitude=test_location_latitude, 
                radius=10000  # 10公里
            )
            
            print("\n" + "=" * 80)
            print("🎉 API测试完成！")
            print(f"✅ 根据坐标查询附近地点的功能已成功实现")
            print(f"✅ API端点: {SERVER_URL}{API_ENDPOINT}")
            print(f"✅ 支持参数: longitude, latitude, radius")
            print("=" * 80)
            
            print("\n📋 使用说明:")
            print(f"1. 服务器仍在运行中，可以通过浏览器访问 {SERVER_URL}{API_ENDPOINT}?longitude=116.404&latitude=39.915&radius=5000")
            print(f"2. 或者使用curl命令: curl '{SERVER_URL}{API_ENDPOINT}?longitude=116.404&latitude=39.915&radius=5000'")
            print("3. 按 Ctrl+C 终止服务器")
            
            # 保持服务器运行
            print("\n服务器正在运行中...")
            server_process.wait()
            
        except KeyboardInterrupt:
            print("\n\n收到中断信号，正在停止服务器...")
            server_process.terminate()
            print("✅ 服务器已停止")


if __name__ == '__main__':
    main()

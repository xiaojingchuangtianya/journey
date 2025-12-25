import time
import os
from django.http import HttpResponseForbidden
from django.core.cache import cache
import logging
import sys
import subprocess

# 配置基本日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger('ip_block_middleware')
logger.setLevel(logging.INFO)

# Nginx阻止IP文件路径
NGINX_BLOCKED_IPS_FILE = '/home/nginx/blocked_ips.conf'

# 配置参数
MAX_FAILED_ATTEMPTS = 3  # 最大失败尝试次数
BLOCK_DURATION = 3600    # 记录保留时长（秒），默认1小时
CACHE_PREFIX = 'ip_access_'
ALLOWED_HOSTS = ['183.63.111.186']  # 允许的host列表，这些host不会被限制



class IpBlockMiddleware:
    """
    IP访问限制中间件
    功能：跟踪每个IP地址访问未命中URL的次数，超过阈值则将IP写入nginx阻止列表
    不再直接拦截请求，拦截工作由nginx负责
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        logger.info("IP访问记录中间件已初始化")
        logger.info(f"中间件配置：最大失败次数={MAX_FAILED_ATTEMPTS}, 记录时长={BLOCK_DURATION}秒")
        logger.info(f"允许的host列表: {ALLOWED_HOSTS}")
        logger.info(f"Nginx阻止IP文件路径: {NGINX_BLOCKED_IPS_FILE}")
        
        # 确保Nginx阻止IP文件目录存在
        os.makedirs(os.path.dirname(NGINX_BLOCKED_IPS_FILE), exist_ok=True)
    
    def __call__(self, request):
        # 检查请求的host是否在允许列表中
        # 获取客户端IP地址
        client_ip = self._get_client_ip(request)
        if client_ip in ALLOWED_HOSTS:
            logger.info(f"IP {client_ip} 在允许列表中，跳过IP限制检查")
            return self.get_response(request)
          
        # 处理请求前进行记录和检查，但不再拦截
        try:
            # 记录访问
            logger.info(f"记录来自IP {client_ip} 的请求，URL: {request.path}")
            
            # 获取当前失败次数
            cache_key = f'{CACHE_PREFIX}failed_{client_ip}'
            current_attempts = cache.get(cache_key, 0)
            logger.info(f"IP {client_ip} 当前失败次数: {current_attempts}/{MAX_FAILED_ATTEMPTS}")
        except Exception as e:
            logger.error(f"记录IP访问时发生错误: {str(e)}", exc_info=True)
        
        try:
            # 处理请求 - 不再直接拦截，全部交给nginx处理
            response = self.get_response(request)
            
            # 检查响应状态码，如果是404（URL未命中），增加失败计数
            if response.status_code == 404:
                logger.warning(f"IP {client_ip} 访问了不存在的URL: {request.path}，将增加失败计数")
                self._increment_failed_attempt(client_ip)
            
            return response
        except Exception as e:
            logger.error(f"处理请求时发生错误: {str(e)}", exc_info=True)
            return self.get_response(request)
    
    def _get_client_ip(self, request):
        """获取客户端真实IP地址"""
        try:
            # 优先从HTTP_X_FORWARDED_FOR获取（如果通过代理）
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                # 多个代理的情况下，取第一个IP
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                # 直接获取REMOTE_ADDR
                ip = request.META.get('REMOTE_ADDR', 'unknown')
            return ip
        except Exception as e:
            logger.error(f"获取IP地址时发生错误: {str(e)}", exc_info=True)
            return 'unknown'
    
    def _increment_failed_attempt(self, ip):
        """增加失败尝试次数，并在超过阈值时记录到nginx阻止列表"""
        try:
            # 获取当前失败次数
            cache_key = f'{CACHE_PREFIX}failed_{ip}'
            attempts = cache.get(cache_key, 0)
            
            # 增加计数
            attempts += 1
            cache.set(cache_key, attempts, BLOCK_DURATION)
            
            # 检查是否超过阈值
            if attempts >= MAX_FAILED_ATTEMPTS:
                logger.warning(f"IP {ip} 失败次数达到阈值 {attempts}/{MAX_FAILED_ATTEMPTS}，将添加到nginx阻止列表")
                
                # 将被阻止的IP写入文件，供Nginx直接拒绝访问
                self._add_ip_to_nginx_blocklist(ip)
        except Exception as e:
            logger.error(f"增加失败计数时发生错误: {str(e)}", exc_info=True)
    
    def _add_ip_to_nginx_blocklist(self, ip):
        """将被阻止的IP添加到Nginx阻止列表文件，并自动执行nginx reload进行热更新"""
        try:
            logger.info(f"正在将IP {ip} 添加到Nginx阻止列表文件")
            
            # 读取现有阻止的IP列表
            blocked_ips = set()
            if os.path.exists(NGINX_BLOCKED_IPS_FILE):
                try:
                    with open(NGINX_BLOCKED_IPS_FILE, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and line.startswith('deny '):
                                # 提取IP地址
                                ip_in_file = line.split()[1].strip(';')
                                blocked_ips.add(ip_in_file)
                except Exception as e:
                    logger.error(f"读取Nginx阻止列表文件时发生错误: {str(e)}")
            
            # 添加新的阻止IP
            blocked_ips.add(ip)
            
            # 写入文件
            with open(NGINX_BLOCKED_IPS_FILE, 'w', encoding='utf-8') as f:
                f.write('# 被阻止的IP地址列表 - 由Django中间件自动生成\n')
                f.write(f'# 最后更新时间: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write('\n')
                for blocked_ip in sorted(blocked_ips):
                    f.write(f'deny {blocked_ip};\n')
            
            logger.info(f"IP {ip} 已添加到Nginx阻止列表文件，当前阻止的IP总数: {len(blocked_ips)}")
            
            # 尝试自动执行nginx reload进行热更新
            try:
                # 在Linux/Unix上执行nginx reload
                subprocess.run(['/home/nginx/sbin/nginx', '-s', 'reload'], check=True)
                logger.info(f"Linux/Unix系统：已成功执行nginx reload，更新了阻止IP列表")
            except Exception as e:
                logger.warning(f"执行nginx reload时发生错误: {str(e)}，请手动执行 '/home/nginx/sbin/nginx -s reload'")
        except Exception as e:
            logger.error(f"将IP添加到Nginx阻止列表文件时发生错误: {str(e)}", exc_info=True)
import time
from django.http import HttpResponseForbidden
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class IpBlockMiddleware:
    """
    IP访问限制中间件
    功能：跟踪每个IP地址访问未命中URL的次数，超过阈值则阻止访问
    """
    
    # 配置参数
    MAX_FAILED_ATTEMPTS = 5  # 最大失败尝试次数
    BLOCK_DURATION = 3600    # 阻止时长（秒），默认1小时
    CACHE_PREFIX = 'ip_access_'
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 获取客户端IP地址
        client_ip = self._get_client_ip(request)
        
        # 检查IP是否已被阻止
        if self._is_ip_blocked(client_ip):
            logger.warning(f"已阻止IP {client_ip} 的访问请求")
            return HttpResponseForbidden("您的IP因多次访问错误地址已被暂时限制访问")
        
        # 处理请求
        response = self.get_response(request)
        
        # 检查响应状态码，如果是404（URL未命中），增加失败计数
        if response.status_code == 404:
            self._increment_failed_attempt(client_ip)
            logger.info(f"IP {client_ip} 访问了不存在的URL")
        
        return response
    
    def _get_client_ip(self, request):
        """获取客户端真实IP地址"""
        # 优先从HTTP_X_FORWARDED_FOR获取（如果通过代理）
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # 多个代理的情况下，取第一个IP
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            # 直接获取REMOTE_ADDR
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _is_ip_blocked(self, ip):
        """检查IP是否已被阻止"""
        cache_key = f'{self.CACHE_PREFIX}blocked_{ip}'
        return cache.get(cache_key) is not None
    
    def _increment_failed_attempt(self, ip):
        """增加失败尝试次数，并在超过阈值时阻止IP"""
        # 获取当前失败次数
        cache_key = f'{self.CACHE_PREFIX}failed_{ip}'
        attempts = cache.get(cache_key, 0)
        
        # 增加计数
        attempts += 1
        cache.set(cache_key, attempts, self.BLOCK_DURATION)  # 缓存失败计数，过期时间与阻止时长一致
        
        # 检查是否超过阈值
        if attempts >= self.MAX_FAILED_ATTEMPTS:
            # 阻止该IP
            block_key = f'{self.CACHE_PREFIX}blocked_{ip}'
            cache.set(block_key, True, self.BLOCK_DURATION)
            logger.warning(f"IP {ip} 已被阻止，原因：连续访问错误地址 {attempts} 次")
            
            # 清除失败计数缓存
            cache.delete(cache_key)

from Journal.models import User
from Journal import models 
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.contrib.contenttypes.models import ContentType
from .models import Like
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
from .models import Comment, Like, Favorite
import math
from django.db.models import Q, Case, When, IntegerField
import difflib
import json
import os
import random
import urllib.request
import json
from django.core.files.base import ContentFile
import os
from urllib.parse import urlparse
from datetime import datetime
from .WXBizDataCrypt import WXBizDataCrypt
from Journey.settings import APP_ID, APP_SECRET

def determine_type(image_count):
    """根据图片数量确定type返回值"""
    if image_count == 1:
        return "single"
    elif image_count == 3:
        return "split"
    elif image_count % 2 == 0:  # 偶数
        return random.choice(["double", "carousel"])
    else:
        # 其他情况默认返回carousel
        return "single"


# 获取前10条的的地点信息
# 规则：获取玩家前10信息时，不会下发，在触发往下拉才开始需要用户进行注册，同理在创作时也会要求用户进行注册
# csrf_token应尽早下发，保证用户在创作时，有对应数据
# 
def JournalMessage(request,startIndex=0):
    # 增加容错处理，后续还会有点赞的数量关联，在此给用户下发csrf_token
    try:
        # 获取所有地点，并按点赞数从高到低排序
        locations_with_likes = []
        # 获取Location模型的ContentType
        location_content_type = ContentType.objects.get_for_model(models.Location)
        
        # 获取所有地点
        all_locations = models.Location.objects.all()
        
        # 为每个地点计算点赞数
        for location in all_locations:
            likes_count = Like.objects.filter(
                content_type=location_content_type,
                object_id=location.id
            ).count()
            locations_with_likes.append((location, likes_count))
        
        # 按点赞数从高到低排序
        locations_with_likes.sort(key=lambda x: x[1], reverse=True)
        
        # 提取排序后的地点对象并进行分页
        locations = [loc for loc, _ in locations_with_likes][startIndex:startIndex+10]
        # 从请求中获取username参数，判断用户是否登录
        username = request.GET.get('username')
        user = None
        
        # 如果提供了username，尝试获取用户对象
        if username:
            try:
                user = models.User.objects.get(username=username)
            except models.User.DoesNotExist:
                user = None
        
        # 根据用户登录状态设置点赞状态
        if user:
            # 已登录用户：查询实际点赞状态
            liked_ids = Like.objects.filter(
                user=user,
                content_type=location_content_type
            ).values_list('object_id', flat=True)
            for location in locations:
                location.isLiked = location.id in liked_ids
        else:
            # 未登录用户：所有地点设置为未点赞
            for location in locations:
                location.isLiked = False
        
        return JsonResponse({
            # 状态
            'status': 'success',
            # csrf_token
            'csrf_token': get_token(request),
            # 数据
            'data': [
                {
                    "id": location.id,
                    'title': location.title,
                    'content': location.content,
                    'created_at': location.created_at.isoformat(),
                    'longitude': location.longitude,#经度
                    'latitude': location.latitude,#纬度
                    'address': location.address,#地点名字
                    'user': location.user.nickname or location.user.username,
                    "images":[request.build_absolute_uri(image.image.url) for image in location.photos.all()],
                    "likes_count": likes_count,
                    "isLiked": location.isLiked,
                    "type": determine_type(location.photos.count()),
                }
                for location in locations
            ]
        })
    except Exception as e:
        # 意外情况处理
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })



# post接口，客户端需要在headers增加X-CSRFToken参数进行下发
# 进入到小程序界面，首次触发创建账号
def createUser(request):
    if request.method == 'POST':
        try:
            # 从POST请求中获取微信授权所需参数
            code = request.POST.get('code')
            encryptedData = request.POST.get('encryptedData')
            iv = request.POST.get('iv')
            ip_location = request.POST.get('ip_location', '')
            
            # 验证必需参数
            if not all([code, encryptedData, iv]):
                return JsonResponse({
                    'status': 'error',
                    'message': '缺少必要的微信授权参数'
                })
                    
            
            # 构建微信登录API请求URL
            wx_login_url = f"https://api.weixin.qq.com/sns/jscode2session?appid={APP_ID}&secret={APP_SECRET}&js_code={code}&grant_type=authorization_code"
            
            # 发送请求获取session_key
            with urllib.request.urlopen(wx_login_url, timeout=10) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode('utf-8'))
                    
                    # 检查是否获取成功
                    if 'errcode' in result:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'获取微信session_key失败: {result.get("errmsg", "未知错误")}'
                        })
                    
                    session_key = result.get('session_key')
                    openid = result.get('openid')
                    
                    if not session_key or not openid:
                        return JsonResponse({
                            'status': 'error',
                            'message': '获取微信session_key或openid失败'
                        })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'请求微信API失败，状态码: {response.status}'
                    })

            # 2. 使用session_key解密encryptedData获取用户信息
            pc = WXBizDataCrypt(APP_ID, session_key)
            try:
                user_info = pc.decrypt(encryptedData, iv)
                print(user_info)
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'解密用户数据失败: {str(e)}'
                })

            # 3. 处理用户头像
            avatar_file = None
            if user_info.get('avatarUrl'):
                try:
                    avatar_url = user_info['avatarUrl']
                    # 下载头像图片
                    req = urllib.request.Request(avatar_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=10) as response:
                        if response.status == 200:
                            # 生成文件名，使用openid和时间戳
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            filename = f"avatar_{openid}_{timestamp}.png"
                            # 保存到Django文件系统
                            avatar_file = ContentFile(response.read(), name=filename)
                except Exception as e:
                    print(f"下载头像失败: {str(e)}")
                    # 如果下载失败，不阻止用户创建，只是不设置头像
                    avatar_file = None
            # 4. 查找或创建用户
            # 使用openid作为username存储
            try:
                user = models.User.objects.get(username=openid)
                # 更新现有用户信息
                user.nickname = user_info.get('nickName', openid)
                user.gender = user_info.get('gender') if user_info.get('gender') else None
                
                # 使用微信用户信息中的province和city构建ip_location
                province = user_info.get('province', '')
                city = user_info.get('city', '')
                
                # 按照province-city格式拼接，如果两个都没有则为空字符串
                if province and city:
                    user.ip_location = f"{province}-{city}"
                elif province:
                    user.ip_location = province
                elif city:
                    user.ip_location = city
                else:
                    user.ip_location = ''
            except models.User.DoesNotExist:
                # 使用微信用户信息中的province和city构建ip_location
                province = user_info.get('province', '')
                city = user_info.get('city', '')
                
                # 按照province-city格式拼接，如果两个都没有则为空字符串
                ip_location_value = ''
                if province and city:
                    ip_location_value = f"{province}-{city}"
                elif province:
                    ip_location_value = province
                elif city:
                    ip_location_value = city
                
                # 创建新用户
                user = models.User.objects.create_user(
                    username=openid,  # 使用openid作为username
                    nickname=user_info.get('nickName', openid),
                    gender=user_info.get('gender') if user_info.get('gender') else None,
                    ip_location=ip_location_value
                )
            # 5. 设置头像
            if avatar_file:
                user.avatar = avatar_file
                user.save()
            
            # 6. 构建返回数据
            avatar_url = request.build_absolute_uri(user.avatar.url) if user.avatar else ''
            
            return JsonResponse({
                'status': 'success',
                'message': '用户登录成功',
                'user': {
                    'username': user.username,  # 返回openid
                    'nickname': user.nickname,
                    'ip_location': user.ip_location,
                    'gender': user.gender,
                    'avatar': avatar_url,
                }
            })
        
        except Exception as e:
            # 捕获所有其他异常并返回错误信息
            print(f"登录过程异常: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'登录失败: {str(e)}'
            })
    else:
        return HttpResponse("Invalid request method")


# 创建地点

def createLocation(request):
    """创建地点视图函数"""
    pass


# 修改地点
#预留接口，但不打算进行实现
def changeLocation(request):
    """修改地点视图函数"""
    pass


# 创建评论

def createComment(request):
    if request.method == 'POST':
        try:
            # 获取必要参数
            content = request.POST.get('content')
            username = request.POST.get('username')
            location_id = request.POST.get('location_id')
            is_parent = request.POST.get('is_parent', True)
            parent_id = request.POST.get('parent') if not is_parent else None
            
            # 验证必要参数
            if not content or not username:
                return JsonResponse({
                    'status': 'error',
                    'message': '内容和用户名不能为空！'
                })
            
            # 获取用户对象
            user = User.objects.get(username=username)
            
            # 获取地点对象（如果提供了location_id）
            location = None
            if location_id:
                location = models.Location.objects.get(id=location_id)
            
            # 获取父评论对象（如果需要）
            parent = None
            if parent_id:
                parent = models.Comment.objects.get(id=parent_id)
            
            # 创建评论
            comment = models.Comment.objects.create(
                content=content,
                is_parent=is_parent,
                parent=parent,
                user=user,
                location=location
            )
            
            return JsonResponse({
                'status': 'success',
                'message': '评论创建成功！！！',
                'comment_id': comment.id
            })
            
        except User.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': '用户不存在！'
            })
        except models.Location.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': '地点不存在！'
            })
        except models.Comment.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': '父评论不存在！'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'创建评论失败：{str(e)}'
            })
    else:
        return JsonResponse({
            'status': 'error',
            'message': '请求方法错误！'
        })


# 展示评论


def showComment(request, location_id):
    """展示评论视图函数，根据地点ID返回所有评论的JSON数据"""
    try:
        # 查询指定地点的所有父级评论，按创建时间降序排列
        comments = Comment.objects.filter(location_id=location_id, is_parent=True).order_by('-created_at')
        # 准备评论数据列表
        comments_data = []
        
        for comment in comments:
            # 获取评论的回复
            replies = comment.replies.all().order_by('created_at')
            replies_data = []
            
            for reply in replies:
                # 获取回复的点赞数
                reply_content_type = ContentType.objects.get_for_model(reply)
                reply_likes_count = Like.objects.filter(
                    content_type=reply_content_type,
                    object_id=reply.id
                ).count()
                
                replies_data.append({
                    'id': reply.id,
                    'content': reply.content,
                    'user': reply.user.nickname,
                    'created_at': reply.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'likes_count': reply_likes_count
                })
            
            # 获取主评论的点赞数
            comment_content_type = ContentType.objects.get_for_model(comment)
            likes_count = Like.objects.filter(
                content_type=comment_content_type,
                object_id=comment.id
            ).count()
            
            comments_data.append({
                'id': comment.id,
                'content': comment.content,
                'user': comment.user.nickname,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'likes_count': likes_count,
                'replies': replies_data
            })
        
        return JsonResponse({
            'status': 'success',
            'data': comments_data,
            'message': '评论获取成功'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'获取评论失败: {str(e)}'
        }, status=400)


# 点赞评论

def likeComment(request):
    """点赞评论视图函数"""
    pass


def toggle_like_location(request):
    """切换地点点赞状态的视图函数
    如果用户已点赞地点，则取消点赞；如果未点赞，则添加点赞
    """
    if request.method == 'POST':
        try:
            # 获取请求参数
            username = request.POST.get('username')
            location_id = request.POST.get('location_id')
            
            # 验证必要参数
            if not username or not location_id:
                return JsonResponse({
                    'status': 'error',
                    'message': '用户名和地点ID不能为空！'
                })
            
            # 获取用户对象
            user = models.User.objects.get(username=username)
            
            # 获取地点对象
            location = models.Location.objects.get(id=location_id)
            
            # 获取地点的ContentType
            location_content_type = ContentType.objects.get_for_model(location)
            
            # 检查用户是否已点赞该地点
            existing_like = models.Like.objects.filter(
                user=user,
                content_type=location_content_type,
                object_id=location.id
            ).first()
            
            if existing_like:
                # 如果已点赞，则取消点赞（删除点赞记录）
                existing_like.delete()
                is_liked = False
                message = '取消点赞成功！'
            else:
                # 如果未点赞，则添加点赞（创建点赞记录）
                models.Like.objects.create(
                    user=user,
                    content_type=location_content_type,
                    object_id=location.id
                )
                is_liked = True
                message = '点赞成功！'
            
            # 获取更新后的点赞数
            likes_count = models.Like.objects.filter(
                content_type=location_content_type,
                object_id=location.id
            ).count()
            
            return JsonResponse({
                'status': 'success',
                'message': message,
                'is_liked': is_liked,
                'likes_count': likes_count
            })
            
        except models.User.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': '用户不存在！'
            })
        except models.Location.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': '地点不存在！'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'操作失败：{str(e)}'
            })
    else:
        return JsonResponse({
            'status': 'error',
            'message': '只支持POST请求！'
        })


def search_locations(request):
    """搜索地点的接口
    支持按标题、内容、地址和昵称进行关键词搜索，并根据关联性排序
    增强了模糊关联搜索能力，支持相似字符串匹配（如输入abc能匹配abd、adb等）
    根据配置文件中的规则计算权重和匹配阈值
    """
    if request.method == 'GET':
        try:
            # 加载搜索配置
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'search_config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                search_config = json.load(f)
            
            # 获取搜索参数
            keyword = request.GET.get('keyword', '').strip()
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            
            # 验证参数
            if page < 1:
                page = 1
            if page_size < 1 or page_size > 50:
                page_size = 10
            
            # 构建查询
            query = models.Location.objects.select_related('user')
            
            if keyword:
                print(f"Debug - Input keyword: {keyword}")
                # 应用所有特殊映射配置：检查并替换关键词中包含的所有特殊映射
                mapped_keyword = keyword
                for special_key, mapped_value in search_config['special_mappings'].items():
                    if special_key in mapped_keyword:
                        original_keyword = mapped_keyword
                        mapped_keyword = mapped_keyword.replace(special_key, mapped_value)
                        print(f"Debug - Applied special mapping: {special_key} -> {mapped_value} in {original_keyword} -> {mapped_keyword}")
                
                # 使用映射后的关键词进行搜索
                keywords = mapped_keyword.split()
                print(f"Debug - Using mapped keywords: {keywords}")
                
                # 获取所有可能的地点进行模糊匹配
                # 先获取所有地点，后续在Python中进行模糊匹配
                # 为了性能考虑，我们可以先做一个简单的过滤
                locations = list(models.Location.objects.select_related('user').all())
                
                # 保存模糊匹配到的地点
                matched_locations = []
                
                # 对每个地点进行模糊匹配检查
                for location in locations:
                    # 标记是否匹配
                    is_matched = False
                    
                    # 对每个关键词进行模糊匹配
                    for kw in keywords:
                        # 计算与标题的相似度
                        title_similarity = difflib.SequenceMatcher(None, kw.lower(), location.title.lower()).ratio()
                        # 计算与地址的相似度
                        address_similarity = difflib.SequenceMatcher(None, kw.lower(), location.address.lower()).ratio()
                        # 计算与昵称的相似度
                        nickname_similarity = difflib.SequenceMatcher(None, kw.lower(), location.user.nickname.lower()).ratio()
                        
                        # 获取配置中的阈值和关键词
                        default_threshold = search_config['similarity_thresholds']['default']
                        special_threshold = search_config['similarity_thresholds']['special_topic']
                        camping_keywords = search_config['related_keywords']['camping']
                        
                        # 检查是否是特殊主题相关的搜索
                        is_special_topic = any(camp_word in kw for camp_word in camping_keywords)
                        target_has_special = any(camp_word in location.title or camp_word in location.address 
                                              for camp_word in camping_keywords)
                        
                        # 动态阈值：如果是特殊主题相关搜索，使用较低的阈值
                        threshold = special_threshold if (is_special_topic or target_has_special) else default_threshold
                        
                        # 如果相似度足够高，或者是精确包含，就认为匹配
                        if (title_similarity >= threshold or address_similarity >= threshold or nickname_similarity >= threshold or
                            kw.lower() in location.title.lower() or kw.lower() in location.address.lower() or 
                            kw.lower() in location.user.nickname.lower()):
                            is_matched = True
                            break
                    
                    # 如果匹配，添加到结果列表
                    if is_matched:
                        matched_locations.append(location)
                
                # 使用匹配到的地点列表
                
                # 为每个地点计算关联度分数
                scored_locations = []
                for location in matched_locations:
                    score = 0
                    
                    # 获取配置中的权重
                    default_weights = search_config['weight_config']['default']
                    special_weights = search_config['weight_config']['special_topic']
                    camping_keywords = search_config['related_keywords']['camping']
                    
                    # 根据匹配位置和匹配程度计算分数
                    # 标题完全匹配（精确匹配）给最高分
                    if keyword.lower() == location.title.lower():
                        score += default_weights['title_exact_match']
                    # 标题中包含关键词
                    elif keyword.lower() in location.title.lower():
                        score += default_weights['title_contains']
                        # 根据关键词在标题中的位置调整分数（越靠前分数越高）
                        title_lower = location.title.lower()
                        kw_lower = keyword.lower()
                        position = title_lower.find(kw_lower)
                        if position != -1:
                            score += max(0, default_weights['title_position_weight'] - position * default_weights['title_position_factor'])
                    # 标题模糊匹配
                    else:
                        # 检查是否是特殊主题相关的搜索
                        is_special_topic = any(camp_word in keyword for camp_word in camping_keywords)
                        target_has_special = any(camp_word in location.title or camp_word in location.address 
                                              for camp_word in camping_keywords)
                        
                        # 计算标题相似度
                        title_similarity = difflib.SequenceMatcher(None, keyword.lower(), location.title.lower()).ratio()
                        
                        # 特殊主题内容特殊处理：降低阈值，提高权重
                        if (is_special_topic and target_has_special):
                            if title_similarity >= search_config['similarity_thresholds']['special_topic']:
                                score += title_similarity * special_weights['title_similarity']
                        # 普通情况
                        elif title_similarity >= search_config['similarity_thresholds']['default']:
                            score += title_similarity * default_weights['title_similarity']
                    
                    # 特殊关键词已经在搜索前替换，这里不再需要额外处理
                    # 保持原有的匹配和计分逻辑
                    
                    # 地址匹配
                    for kw in keywords:
                        if kw.lower() in location.address.lower():
                            score += default_weights['address_contains']
                            # 地址中的关键词也考虑位置
                            address_lower = location.address.lower()
                            position = address_lower.find(kw.lower())
                            if position != -1:
                                score += max(0, default_weights['address_position_weight'] - position * default_weights['address_position_factor'])
                        # 地址模糊匹配
                        else:
                            # 检查是否是特殊主题相关的关键词
                            is_special_kw = any(camp_word in kw for camp_word in camping_keywords)
                            address_has_special = any(camp_word in location.address for camp_word in camping_keywords)
                            
                            address_similarity = difflib.SequenceMatcher(None, kw.lower(), location.address.lower()).ratio()
                            
                            # 特殊主题地址特殊处理
                            if (is_special_kw and address_has_special):
                                if address_similarity >= search_config['similarity_thresholds']['special_topic']:
                                    score += address_similarity * special_weights['address_similarity']
                            elif address_similarity >= search_config['similarity_thresholds']['default']:
                                score += address_similarity * default_weights['address_similarity']
                    
                    # 内容匹配
                    content_lower = location.content.lower()
                    for kw in keywords:
                        if kw.lower() in content_lower:
                            # 内容匹配的权重较低，但匹配次数越多分数越高
                            match_count = content_lower.count(kw.lower())
                            score += default_weights['content_contains_base'] + (match_count - 1) * default_weights['content_contains_factor']
                        # 内容模糊匹配
                        else:
                            # 检查是否是特殊主题相关的关键词
                            is_special_kw = any(camp_word in kw for camp_word in camping_keywords)
                            content_has_special = any(camp_word in location.content for camp_word in camping_keywords)
                            
                            content_similarity = difflib.SequenceMatcher(None, kw.lower(), content_lower).ratio()
                            
                            # 特殊主题内容特殊处理
                            if (is_special_kw and content_has_special):
                                if content_similarity >= search_config['similarity_thresholds']['special_topic']:
                                    score += content_similarity * special_weights['content_similarity']
                            elif content_similarity >= search_config['similarity_thresholds']['default']:
                                score += content_similarity * default_weights['content_similarity']
                    
                    # 用户相关字段匹配（仅保留昵称）
                    # 昵称完全匹配
                    if keyword.lower() == location.user.nickname.lower():
                        score += default_weights['nickname_exact_match']
                    # 昵称包含关键词
                    elif keyword.lower() in location.user.nickname.lower():
                        score += default_weights['nickname_contains']
                        # 昵称中的关键词也考虑位置
                        nickname_lower = location.user.nickname.lower()
                        position = nickname_lower.find(keyword.lower())
                        if position != -1:
                            score += max(0, default_weights['nickname_position_weight'] - position * default_weights['nickname_position_factor'])
                    # 昵称模糊匹配
                    else:
                        nickname_similarity = difflib.SequenceMatcher(None, keyword.lower(), location.user.nickname.lower()).ratio()
                        if nickname_similarity >= search_config['similarity_thresholds']['default']:
                            score += nickname_similarity * default_weights['nickname_similarity']
                    
                    # 检查多关键词在昵称中的匹配
                    for kw in keywords:
                        # 昵称中的关键词匹配
                        if kw.lower() in location.user.nickname.lower():
                            score += default_weights['nickname_multi_keywords']
                        # 昵称模糊匹配
                        else:
                            kw_nickname_similarity = difflib.SequenceMatcher(None, kw.lower(), location.user.nickname.lower()).ratio()
                            if kw_nickname_similarity >= search_config['similarity_thresholds']['default']:
                                score += kw_nickname_similarity * default_weights['nickname_multi_keywords_similarity']
                    
                    scored_locations.append((location, score))
                
                # 按关联度分数降序排序，分数相同时按创建时间降序
                scored_locations.sort(key=lambda x: (x[1], x[0].created_at), reverse=True)
                
                # 提取排序后的地点列表
                sorted_locations = [loc for loc, score in scored_locations]
                
                # 计算总数
                total_count = len(sorted_locations)
                
                # 分页
                start = (page - 1) * page_size
                end = start + page_size
                locations = sorted_locations[start:end]
            else:
                # 无关键词时按创建时间降序
                query = query.order_by('-created_at')
                
                # 计算总数
                total_count = query.count()
                
                # 分页
                start = (page - 1) * page_size
                end = start + page_size
                locations = query[start:end]
            
            # 准备返回数据
            search_results = []
            for location in locations:
                # 获取地点的所有图片，随机返回一张
                photos = list(location.photos.all())
                if photos:
                    import random
                    random_photo = random.choice(photos)
                    main_photo_url = request.build_absolute_uri(random_photo.image.url)
                else:
                    main_photo_url = None
                
                # 获取地点的点赞数
                location_content_type = ContentType.objects.get_for_model(location)
                likes_count = models.Like.objects.filter(
                    content_type=location_content_type,
                    object_id=location.id
                ).count()
                
                search_results.append({
                    'id': location.id,
                    'title': location.title,
                    'address': location.address,
                    'content': location.content[:100] + '...' if len(location.content) > 100 else location.content,
                    'longitude': location.longitude,
                    'latitude': location.latitude,
                    'created_at': location.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'main_photo_url': main_photo_url,
                    'likes_count': likes_count,
                    'comments_count': location.comments.count(),
                    'user_nickname': location.user.nickname
                })
            
            # 计算总页数
            total_pages = (total_count + page_size - 1) // page_size
            
            return JsonResponse({
                'status': 'success',
                'message': '搜索成功',
                'data': {
                    'locations': search_results,
                    'total_count': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': total_pages
                }
            })
            
        except ValueError:
            return JsonResponse({
                'status': 'error',
                'message': '分页参数格式错误'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'搜索失败：{str(e)}'
            })
    else:
        return JsonResponse({
            'status': 'error',
            'message': '只支持GET请求'
        })


def get_nearby_locations(request):
    """
    根据用户提供的经纬度坐标返回附近的地点
    URL: /api/nearby-locations/?longitude=经度&latitude=纬度&radius=半径(米)
    默认半径为5000米(5公里)
    """
    if request.method == 'GET':
        try:
            # 获取请求参数
            longitude = float(request.GET.get('longitude', 0))
            latitude = float(request.GET.get('latitude', 0))
            radius = float(request.GET.get('radius', 5000))  # 默认5000米
            
            # 验证经纬度有效性
            if not (-180 <= longitude <= 180) or not (-90 <= latitude <= 90):
                return JsonResponse({
                    'status': 'error',
                    'message': '无效的经纬度坐标'
                }, status=400)
            
            # 获取所有有经纬度的地点
            locations_with_coords = models.Location.objects.filter(
                Q(longitude__isnull=False) & Q(latitude__isnull=False)
            )
            
            # 计算每个地点与用户坐标的距离，并筛选在半径内的地点
            nearby_locations = []
            for location in locations_with_coords:
                # 使用Haversine公式计算两点间距离
                distance = calculate_distance(
                    latitude, longitude, 
                    location.latitude, location.longitude
                )
                
                if distance <= radius:
                    # 获取地点的主图
                    main_photo = location.photos.filter(is_main=True).first()
                    main_photo_url = request.build_absolute_uri(main_photo.image.url) if main_photo else None
                    
                    # 获取地点的点赞数
                    location_content_type = ContentType.objects.get_for_model(location)
                    likes_count = Like.objects.filter(
                        content_type=location_content_type,
                        object_id=location.id
                    ).count()
                    
                    nearby_locations.append({
                        'id': location.id,
                        'title': location.title,
                        'address': location.address,
                        'distance': round(distance, 2),  # 距离，保留两位小数
                        'longitude': location.longitude,
                        'latitude': location.latitude,
                        'main_photo_url': main_photo_url,
                        'likes_count': likes_count,
                        'comments_count': location.comments.count(),
                        'created_at': location.created_at.isoformat()
                    })
            
            # 按距离从小到大排序
            nearby_locations.sort(key=lambda x: x['distance'])
            
            return JsonResponse({
                'status': 'success',
                'data': nearby_locations,
                'message': f'成功获取{len(nearby_locations)}个附近地点',
                'query_params': {
                    'longitude': longitude,
                    'latitude': latitude,
                    'radius': radius
                }
            })
            
        except ValueError:
            return JsonResponse({
                'status': 'error',
                'message': '经纬度或半径参数格式错误，请提供数字'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'获取附近地点失败: {str(e)}'
            }, status=500)
    else:
        return JsonResponse({
            'status': 'error',
            'message': '只支持GET请求'
        }, status=405)


def get_location_detail(request, location_id):
    """
    获取地点详情接口
    返回指定id地点的详细信息，包括id、title、content、longitude、latitude、address、user、images等数据
    """
    try:
        # 尝试获取指定id的地点
        location = models.Location.objects.get(id=location_id)
        
        # 获取用户登录状态
        username = request.GET.get('username')
        print(username)
        # 如果提供了username，尝试获取用户对象
        if username:
            try:
                user = models.User.objects.get(username=username)
            except models.User.DoesNotExist:
                user = None
        
        # 获取地点的ContentType
        location_content_type = ContentType.objects.get_for_model(models.Location)
        
        # 设置点赞状态
        is_liked = False
        if user:
            # 已登录用户：查询实际点赞状态
            is_liked = Like.objects.filter(
                user=user,
                content_type=location_content_type,
                object_id=location.id
            ).exists()
        
        # 获取地点关联的评论
        comments = []
        # 查询该地点的所有父级评论，按创建时间降序排列
        parent_comments = Comment.objects.filter(location=location, is_parent=True).order_by('-created_at')
        
        for comment in parent_comments:
            # 获取评论的回复
            replies = []
            for reply in comment.replies.all().order_by('created_at'):
                # 获取回复的点赞数
                reply_content_type = ContentType.objects.get_for_model(reply)
                reply_likes_count = Like.objects.filter(
                    content_type=reply_content_type,
                    object_id=reply.id
                ).count()
                
                replies.append({
                    'id': reply.id,
                    'content': reply.content,
                    'user': reply.user.nickname or reply.user.username,
                    'created_at': reply.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'likes_count': reply_likes_count
                })
            
            # 获取主评论的点赞数
            comment_content_type = ContentType.objects.get_for_model(comment)
            likes_count = Like.objects.filter(
                content_type=comment_content_type,
                object_id=comment.id
            ).count()
            # 默认头像
            comments.append({
                "avatar": request.build_absolute_uri(comment.user.avatar.url) if comment.user.avatar else None,
                'id': comment.id,
                'content': comment.content,
                'user': comment.user.nickname or comment.user.username,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'likes_count': likes_count,
                'replies': replies
            })
        
        # 获取地点的点赞数
        location_content_type = ContentType.objects.get_for_model(location)
        likes_count = Like.objects.filter(
            content_type=location_content_type,
            object_id=location.id
        ).count()
        
        # 构建返回数据
        location_data = {
            "id": location.id,
            "title": location.title,
            "content": location.content,
            "longitude": location.longitude,  # 经度
            "latitude": location.latitude,    # 纬度
            "address": location.address,      # 地点名字
            "user":  location.user.username,
            "images": [request.build_absolute_uri(image.image.url) for image in location.photos.all()],
            "likes_count": likes_count,
            "isCollected": location.user.favorites.filter(user=user, location=location).exists(),
            "isLiked": is_liked,
            "created_at": location.created_at.isoformat(),
            "comments": comments
        }
        
        return JsonResponse({
            'status': 'success',
            "csrf_token": get_token(request),
            'data': location_data
        })
    except models.Location.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': '地点不存在'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'获取地点详情失败: {str(e)}'
        }, status=500)


def toggle_favorite(request):
    """
    收藏/取消收藏地点接口
    使用POST请求，需要提供username和location_id参数
    """
    if request.method == 'POST':
        try:
            # 获取请求参数
            username = request.POST.get('username')
            location_id = request.POST.get('location_id')
            
            # 参数验证
            if not username:
                return JsonResponse({
                    'status': 'error',
                    'message': '用户名不能为空'
                }, status=400)
            
            if not location_id:
                return JsonResponse({
                    'status': 'error',
                    'message': '地点ID不能为空'
                }, status=400)
            
            # 尝试获取用户
            try:
                user = models.User.objects.get(username=username)
            except models.User.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': '用户不存在'
                }, status=404)
            
            # 尝试获取地点
            try:
                location = models.Location.objects.get(id=location_id)
            except models.Location.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': '地点不存在'
                }, status=404)
            
            # 检查是否已经收藏
            favorite, created = Favorite.objects.get_or_create(user=user, location=location)
            
            if not created:
                # 已经收藏，取消收藏
                favorite.delete()
                return JsonResponse({
                    'status': 'success',
                    'message': '取消收藏成功',
                    'is_favorited': False
                })
            else:
                # 新收藏
                return JsonResponse({
                    'status': 'success',
                    'message': '收藏成功',
                    'is_favorited': True
                })
                
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'参数错误: {str(e)}'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'操作失败: {str(e)}'
            }, status=500)
    else:
        return JsonResponse({
            'status': 'error',
            'message': '只支持POST请求'
        }, status=405)


def check_favorite_status(request):
    """
    检查用户是否收藏了某个地点的接口
    使用GET请求，需要提供username和location_id参数
    """
    if request.method == 'GET':
        try:
            # 获取请求参数
            username = request.GET.get('username')
            location_id = request.GET.get('location_id')
            
            # 参数验证
            if not username or not location_id:
                return JsonResponse({
                    'status': 'error',
                    'message': '用户名和地点ID不能为空'
                }, status=400)
            
            # 尝试获取用户
            try:
                user = models.User.objects.get(username=username)
            except models.User.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': '用户不存在'
                }, status=404)
            
            # 尝试获取地点
            try:
                location = models.Location.objects.get(id=location_id)
            except models.Location.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': '地点不存在'
                }, status=404)
            
            # 检查是否已经收藏
            is_favorited = Favorite.objects.filter(user=user, location=location).exists()
            
            # 获取收藏数量
            favorites_count = Favorite.objects.filter(location=location).count()
            
            return JsonResponse({
                'status': 'success',
                'data': {
                    'is_favorited': is_favorited,
                    'favorites_count': favorites_count
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'查询失败: {str(e)}'
            }, status=500)
    else:
        return JsonResponse({
            'status': 'error',
            'message': '只支持GET请求'
        }, status=405)


def get_user_favorites(request, username):
    """
    获取用户收藏的所有地点接口
    使用GET请求，通过URL路径参数提供username
    """
    if request.method == 'GET':
        try:
            # 尝试获取用户
            try:
                user = models.User.objects.get(username=username)
            except models.User.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': '用户不存在'
                }, status=404)
            
            # 获取用户收藏的所有地点
            favorites = Favorite.objects.filter(user=user).order_by('-created_at')
            
            # 构建返回数据
            favorite_locations = []
            location_content_type = ContentType.objects.get_for_model(models.Location)
            
            for favorite in favorites:
                location = favorite.location
                # 获取点赞数
                likes_count = Like.objects.filter(
                    content_type=location_content_type,
                    object_id=location.id
                ).count()
                
                # 获取主图URL
                main_photo = location.photos.filter(is_main=True).first()
                main_photo_url = request.build_absolute_uri(main_photo.image.url) if main_photo else None
                
                favorite_locations.append({
                    'id': location.id,
                    'title': location.title,
                    'content': location.content,
                    'address': location.address,
                    'longitude': location.longitude,
                    'latitude': location.latitude,
                    'user': location.user.nickname or location.user.username,
                    'main_photo_url': main_photo_url,
                    'likes_count': likes_count,
                    'comments_count': location.comments.count(),
                    'favorited_at': favorite.created_at.isoformat(),
                    'created_at': location.created_at.isoformat()
                })
            
            return JsonResponse({
                'status': 'success',
                'data': favorite_locations,
                'total': len(favorite_locations)
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'获取收藏列表失败: {str(e)}'
            }, status=500)
    else:
        return JsonResponse({
            'status': 'error',
            'message': '只支持GET请求'
        }, status=405)

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    使用Haversine公式计算两点间的距离（单位：米）
    Haversine公式考虑了地球的曲率，适合计算较长距离
    """
    # 地球半径（米）
    R = 6371000
    
    # 转换为弧度
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    # Haversine公式
    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # 计算距离
    distance = R * c
    return distance


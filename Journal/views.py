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
from django.db.models import Q
import random
import requests
from django.core.files.base import ContentFile
import os
from urllib.parse import urlparse

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
            # 获取并处理username参数
            username_data = request.POST.getlist('username')
            username = username_data[0].strip() if username_data and username_data[0] else None
            
            # 获取并处理avatar参数
            avatar_data = request.POST.getlist('avatar')
            avatar_file = None
            if avatar_data and avatar_data[0]:
                # 清理avatar字符串中的额外空格和引号
                avatar_url = avatar_data[0].strip().strip('`"\'')
                if avatar_url:
                    try:
                        # 下载图片
                        response = requests.get(avatar_url, timeout=10)
                        if response.status_code == 200:
                            # 从URL获取文件名
                            parsed_url = urlparse(avatar_url)
                            filename = os.path.basename(parsed_url.path)
                            # 如果URL没有文件名，生成一个默认名称
                            if not filename:
                                filename = f"avatar_{username}_{random.randint(1000, 9999)}.jpg"
                            # 保存到Django文件系统
                            avatar_file = ContentFile(response.content, name=filename)
                    except Exception as e:
                        print(f"下载头像失败: {str(e)}")
                        # 如果下载失败，不阻止用户创建，只是不设置头像
                        avatar_file = None

            # 获取并处理gender参数
            gender_data = request.POST.getlist('gender')
            gender = gender_data[0] if gender_data and gender_data[0] else None
            
            # 获取ip_location参数
            ip_location_data = request.POST.getlist('ip_location')
            ip_location = ip_location_data[0] if ip_location_data else ''
            
            # 验证必需参数
            if not username:
                return JsonResponse({
                    'status': 'error',
                    'message': '用户名不能为空'
                })
            
            # 创建用户
            user = models.User.objects.create_user(
                username=username,
                nickname=username,  # 使用username作为nickname
                ip_location=ip_location,
                gender=gender
            )
            
            # 设置头像（单独设置以避免create_user方法可能的限制）
            if avatar_file:
                user.avatar = avatar_file
                user.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'User created successfully',
                'user': {
                    'username': user.username,
                    'nickname': user.nickname,
                    'ip_location': user.ip_location,
                    'gender': user.gender,
                    'avatar': user.avatar,
                }
            })
        except models.User.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': '用户不存在'
            })
        except Exception as e:
            # 捕获所有其他异常并返回错误信息
            return JsonResponse({
                'status': 'error',
                'message': f'创建用户失败: {str(e)}'
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
        print(request.POST.get('user_id'))
        print(request.POST.get('location_id'))
        try:
            # 获取必要参数
            content = request.POST.get('content')
            user_id = request.POST.get('user_id')
            location_id = request.POST.get('location_id')
            is_parent = request.POST.get('is_parent', True)
            parent_id = request.POST.get('parent') if not is_parent else None
            
            # 验证必要参数
            if not content or not user_id:
                return JsonResponse({
                    'status': 'error',
                    'message': '内容和用户ID不能为空！'
                })
            
            # 获取用户对象
            user = User.objects.get(id=user_id)
            
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
        user = None
        
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
            "user": location.user.nickname or location.user.username,
            "images": [request.build_absolute_uri(image.image.url) for image in location.photos.all()],
            "likes_count": likes_count,
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


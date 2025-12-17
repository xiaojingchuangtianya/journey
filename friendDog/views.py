from django.shortcuts import render,HttpResponse
from django.http import JsonResponse
from django.contrib.auth.models import User
import json
from datetime import datetime
from .models import DogProfile, DogWalkRecord, DogWalkPhoto, DogAvatar



# Create your views here.
def home(request):
    return JsonResponse({'message': 'Hello, World!'})


def get_dog_info(request, dog_id):
    """
    根据狗的ID返回对应狗的信息
    """
    try:
        # 查询指定ID的狗信息
        dog = DogProfile.objects.get(id=dog_id)
        
        # 构建响应数据
        dog_data = {
            'id': dog.id,
            'nickname': dog.nickname,
            'breed': dog.breed,
            'birth_date': dog.birth_date.strftime('%Y-%m-%d') if dog.birth_date else None,
            'age': calculate_age(dog.birth_date) if dog.birth_date else None,
            'gender': dog.gender,
            'marital_status': dog.marital_status,
            'bio': dog.bio,
            'location': dog.location,
            'mbti': dog.mbti,
            'owner': dog.owner.id if dog.owner else None,
            'created_at': dog.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': dog.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 如果有头像，添加头像URL
        if hasattr(dog, 'avatar') and dog.avatar:
            dog_data['avatar'] = dog.avatar.image.url if dog.avatar.image else None
        
        return JsonResponse({'success': True, 'data': dog_data})
    except DogProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Dog not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def get_walk_records(request):
    """
    获取最近10条遛狗记录
    """
    try:
        # 获取最近10条记录，按创建时间倒序
        records = DogWalkRecord.objects.all().order_by('-created_at')[:10]
        records_data = []
        
        for record in records:
            record_data = {
                'id': record.id,
                'dog_profile': record.dog_profile.id if record.dog_profile else None,
                'start_time': record.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': record.end_time.strftime('%Y-%m-%d %H:%M:%S') if record.end_time else None,
                'location': record.location,
                'distance': record.distance,
                'weather': record.weather,
                'mood': record.mood,
                'user': record.user.id if record.user else None,
                'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': record.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            # 添加遛狗照片信息
            photos = []
            for photo in record.photos.all():
                photos.append({
                    'id': photo.id,
                    'image_url': photo.image.url if photo.image else None
                })
            record_data['photos'] = photos
            records_data.append(record_data)
        
        return JsonResponse({'success': True, 'data': records_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def calculate_age(birth_date):
    """
    根据出生日期计算年龄，返回格式为'X岁Y个月'或'X个月'
    """
    now = datetime.now().date()
    # 如果生日是今天之后，减去一年
    if (now.month, now.day) < (birth_date.month, birth_date.day):
        years = now.year - birth_date.year - 1
        months = now.month - birth_date.month + 12
    else:
        years = now.year - birth_date.year
        months = now.month - birth_date.month
    
    # 根据计算结果格式化输出
    if years > 0:
        return f"{years}岁{months}个月"
    else:
        return f"{months}个月"


def get_walk_record_detail(request, record_id):
    """
    根据ID获取单个遛狗记录详情
    """
    try:
        record = DogWalkRecord.objects.get(id=record_id)
        
        # 构建响应数据
        record_data = {
            'id': record.id,
            'dog_profile': record.dog_profile.id if record.dog_profile else None,
            'start_time': record.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': record.end_time.strftime('%Y-%m-%d %H:%M:%S') if record.end_time else None,
            'location': record.location,
            'distance': record.distance,
            'weather': record.weather,
            'mood': record.mood,
            'user': record.user.id if record.user else None,
            'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': record.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 添加遛狗照片信息
        photos = []
        for photo in record.photos.all():
            photos.append({
                'id': photo.id,
                'image_url': photo.image.url if photo.image else None
            })
        record_data['photos'] = photos
        
        return JsonResponse({'success': True, 'data': record_data})
    except DogWalkRecord.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Walk record not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def create_walk_record(request):
    """
    创建新的遛狗记录
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        # 解析请求体数据
        data = json.loads(request.body)
        
        # 获取关联的狗资料
        dog_profile_id = data.get('dog_profile_id')
        dog_profile = DogProfile.objects.get(id=dog_profile_id) if dog_profile_id else None
        
        # 获取用户信息
        user_id = data.get('user_id')
        user = User.objects.get(id=user_id) if user_id else None
        
        # 创建遛狗记录
        walk_record = DogWalkRecord.objects.create(
            dog_profile=dog_profile,
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            location=data.get('location'),
            distance=data.get('distance'),
            weather=data.get('weather'),
            mood=data.get('mood'),
            user=user
        )
        
        # 注意：文件上传需要特殊处理，这里暂时不处理文件上传
        # 实际应用中需要使用request.FILES来处理文件上传
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': walk_record.id,
                'message': 'Walk record created successfully'
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except DogProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Dog profile not found'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def create_dog_profile(request):
    """
    新增狗信息
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        # 解析请求体数据
        data = json.loads(request.body)
        
        # 获取用户信息
        user_id = data.get('owner_id')
        owner = User.objects.get(id=user_id) if user_id else None
        
        # 创建狗信息
        dog_profile = DogProfile.objects.create(
            nickname=data.get('nickname'),
            breed=data.get('breed'),
            birth_date=data.get('birth_date'),
            gender=data.get('gender'),
            marital_status=data.get('marital_status'),
            bio=data.get('bio'),
            location=data.get('location'),
            mbti=data.get('mbti'),
            owner=owner
        )
        
        # 注意：头像上传需要特殊处理，这里暂时不处理文件上传
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': dog_profile.id,
                'message': 'Dog profile created successfully'
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Owner not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

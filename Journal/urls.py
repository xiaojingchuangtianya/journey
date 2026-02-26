from django.urls import path
from Journal import views

urlpatterns = [
    path('', views.JournalMessage, name='home'),
    path('location/<int:location_id>/', views.get_location_detail, name='地点详情'),
    path('createUser/', views.createUser, name='创建账号'),
    path('createComment/', views.createComment, name='创建评论'),
    path('user-favorites/<str:username>/', views.get_user_favorites, name='获取用户收藏列表'),
    path('toggle-favorite/', views.toggle_favorite, name='切换收藏状态'),
    path('toggle_location_like/', views.toggle_location_like, name='切换地点点赞状态'),
    path('createLocation/', views.createLocation, name='创建地点'),
    path('updateUser/', views.updateUser, name='更新用户信息'),
    path('changeLocation/', views.changeLocation, name='修改调整'),
    path('showComment/<int:location_id>/', views.showComment, name='展示评论'),
    path('likeComment/', views.likeComment, name='点赞评论'),
    path('api/nearby-locations/', views.get_nearby_locations, name='获取附近地点'),
    
    # 收藏相关接口
    path('toggle-favorite/', views.toggle_favorite, name='切换收藏状态'),
    path('check-favorite/', views.check_favorite_status, name='检查收藏状态'),
    path('user-favorites/<str:username>/', views.get_user_favorites, name='获取用户收藏列表'),
    path('searchLocations/', views.search_locations, name='搜索地点'),
]
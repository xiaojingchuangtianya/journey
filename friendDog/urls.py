from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dog/<int:dog_id>/', views.get_dog_info, name='狗的信息'),
    path('walk-records/', views.get_walk_records, name='遛狗信息（10条）'),
    path('walk-record/<int:record_id>/', views.get_walk_record_detail, name='遛狗单条信息'),
    path('walk-record/create/', views.create_walk_record, name='create_walk_record'),
    path('dog/create/', views.create_dog_profile, name='create_dog_profile'),
]
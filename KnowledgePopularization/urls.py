# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.knowledge_index, name='knowledge_index'),
    path('physiology/', views.physiology_knowledge, name='physiology_knowledge'),
    path('psychology/', views.psychology_knowledge, name='psychology_knowledge'),
    path('safety/', views.safety_knowledge, name='safety_knowledge'),
    path('video1/', views.video1, name='video1'),
    path('video2/', views.video2, name='video2'),
]

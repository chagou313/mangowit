from django.urls import path
from . import views



urlpatterns = [
    path('', views.education_index, name='education_index'),
    path('news1/', views.news1, name='news1'),
    path('news2/', views.news2, name='news2'),
    path('news3/', views.news3, name='news3'),
    path('law1/', views.law1, name='law1'),
    path('law2/', views.law2, name='law2'),
    path('law3/', views.law3, name='law3'),
]

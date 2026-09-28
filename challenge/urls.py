# mangowit/challenge/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 配置指向 question1.html 的 URL
    path('category_select/', views.category_select, name='category_select'),
    path('question/', views.question, name='question'),
    path('question1/', views.question1, name='question1'),
    # 可以根据需要添加更多的URL路由，例如question21、question23等
    path('question2/', views.question2, name='question2'),
    path('question3/', views.question3, name='question3'),
    path('question21/', views.question21, name='question21'),
    path('question22/', views.question22, name='question22'),
    # 可以根据需要添加更多的URL路由，例如question21、question23等
    path('question23/', views.question23, name='question23'),
    path('question31/', views.question31, name='question31'),
    path('question32/', views.question32, name='question32'),
    path('question33/', views.question33, name='question33'),
    # 可以根据需要添加更多的URL路由，例如question21、question23等
    path('result/', views.result, name='result'),
    path('level_select/', views.level_select, name='level_select'),
    path('level_select/<str:category>/', views.level_select, name='level_select'),

]
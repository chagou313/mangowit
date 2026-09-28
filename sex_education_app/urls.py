from django.contrib import admin
from django.urls import path
from .views import index, knowledge, news, quiz, community, profile, login_register, physiological_knowledge, psychological_knowledge, safety_knowledge, user_logout,quiz_history,favorite_news,category_select
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', index, name='index'),
    path('knowledge/', knowledge, name='knowledge'),
    path('news/', news, name='news'),
    path('quiz/', quiz, name='quiz'),
    path('community/', community, name='community'),
    path('profile/', profile, name='profile'),
    path('login_register/', login_register, name='login_register'),
    path('knowledge/physiological_knowledge/', physiological_knowledge, name='physiological_knowledge'),
    path('knowledge/psychological_knowledge/', psychological_knowledge, name='psychological_knowledge'),
    path('knowledge/safety_knowledge/', safety_knowledge, name='safety_knowledge'),
    path('logout/', user_logout, name='logout'),  # 新增退出登录的 URL 映射
    path('quiz_history/', quiz_history, name='quiz_history'),
    path('favorite_news/', favorite_news, name='favorite_news'),
    path('category_select/',category_select, name='category_select'),
]

# 开发环境下配置媒体文件访问
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
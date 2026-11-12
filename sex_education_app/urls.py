from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import (
    category_select, community, favorite_news, index, knowledge, login_register,
    news, profile, quiz_history, user_logout,
)

urlpatterns = [
    path('', index, name='index'),
    path('knowledge/', knowledge, name='knowledge'),
    path('news/', news, name='news'),
    path('community/', community, name='community'),
    path('profile/', profile, name='profile'),
    path('login_register/', login_register, name='login_register'),
    path('logout/', user_logout, name='logout'),
    path('quiz_history/', quiz_history, name='quiz_history'),
    path('favorite_news/', favorite_news, name='favorite_news'),
    path('category_select/', category_select, name='category_select'),
]

# 开发环境下配置媒体文件访问
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
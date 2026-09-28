
from django.contrib import admin
from django.urls import path


from django.contrib import admin
from django.urls import path, include
from AI_communication import views as ai_views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('sex_education_app.urls')),
    path('', include('challenge.urls')),
    path('', include('KnowledgePopularization.urls')),
    path('education/', include('EducationInformation.urls')),  # 修改为include
    path('community/', include('CommunityForums.urls')),  # 修改为include
    path('ai/', include('AI_communication.urls')),  # 包含子应用的 urls.py
]


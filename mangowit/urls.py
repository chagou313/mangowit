from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('sex_education_app.urls')),
    path('', include('challenge.urls')),
    path('', include('KnowledgePopularization.urls')),
    path('education/', include('EducationInformation.urls')),
    path('community/', include('CommunityForums.urls')),
    path('ai/', include('AI_communication.urls')),
    path('comments/', include('interactions.urls')),
]


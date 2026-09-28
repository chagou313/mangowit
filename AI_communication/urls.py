from django.urls import path
from . import views

urlpatterns = [
    path('', views.ai_home, name='ai_home'),
    path('get_answer/', views.get_answer, name='get_answer'),
    path('add_question/', views.add_question, name='add_question'),
]

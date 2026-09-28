from django.urls import path
from. import views

urlpatterns = [
    path('', views.community_index, name='community_index'),
    path('publish_topic/', views.publish_topic, name='publish_topic'),
    path('sexual_impulse/', views.sexual_impulse, name='sexual_impulse'),
    path('topic_detail/<int:topic_id>/', views.topic_detail, name='topic_detail'),
]

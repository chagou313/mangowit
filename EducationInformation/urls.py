from django.urls import path
from . import views



urlpatterns = [
    path('', views.education_index, name='education_index'),
    path('item/<int:pk>/', views.news_item, name='news_item'),
    path('law/<slug:slug>/', views.law_detail, name='law_detail'),
    path('news1/', views.news1, name='news1'),
    path('news2/', views.news2, name='news2'),
    path('news3/', views.news3, name='news3'),
    path('law1/', views.law1, name='law1'),
    path('law2/', views.law2, name='law2'),
    path('law3/', views.law3, name='law3'),
    path('react/<slug:article>/<slug:kind>/', views.toggle_reaction, name='toggle_reaction'),
]

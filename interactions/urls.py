from django.urls import path

from . import views

urlpatterns = [
    path("<slug:target>/", views.post_comment, name="post_comment"),
]

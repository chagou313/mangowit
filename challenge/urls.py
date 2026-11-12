from django.urls import path

from . import views

urlpatterns = [
    path('level_select/', views.level_select, name='level_select_root'),
    path('level_select/<str:category>/', views.level_select, name='level_select'),
    path('quiz/result/', views.result, name='quiz_result'),
    path('quiz/<slug:category>/<int:level>/', views.play, name='quiz_play'),
    path('quiz/<slug:category>/<int:level>/answer/', views.answer, name='quiz_answer'),
    # Old hand-written question pages, kept so saved links still land somewhere useful.
    path('question/', views.legacy_question, name='question'),
    path('result/', views.legacy_question, name='result'),
] + [
    path(f'question{n}/', views.legacy_question, name=f'question{n}')
    for n in ("1", "2", "3", "21", "22", "23", "31", "32", "33")
]

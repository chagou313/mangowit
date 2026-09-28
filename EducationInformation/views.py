from django.shortcuts import render, get_object_or_404
from .models import Article

def education_index(request):
    articles = Article.objects.all()[:5]
    return render(request, 'education_index.html', {'articles': articles})

# 更安全的实现方式
def news1(request):
    return render(request, 'news1.html', {
        'official_url': 'https://www.toutiao.com/article/7492683601142759945/'
    })


def news2(request):
    return render(request, 'news2.html')

def news3(request):
    return render(request, 'news3.html')

def law1(request):
    return render(request, 'law1.html')

def law2(request):
    return render(request, 'law2.html')

def law3(request):
    return render(request, 'law3.html')

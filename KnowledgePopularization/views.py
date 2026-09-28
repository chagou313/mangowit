# views.py
from django.shortcuts import render

def knowledge_index(request):
    return render(request, 'knowledge_index.html')

def physiology_knowledge(request):
    return render(request, 'physiology_knowledge.html')

def psychology_knowledge(request):
    return render(request, 'psychology_knowledge.html')

def safety_knowledge(request):
    return render(request, 'safety_knowledge.html')

def video1(request):
    return render(request, 'video1.html')

def video2(request):
    return render(request, 'video2.html')
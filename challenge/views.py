from django.shortcuts import redirect, render


def category_select(request):
    return render(request, "category_select.html")


def question(request):
    return redirect("category_select")


def question1(request):
    return render(request, "question1.html")


def question2(request):
    return render(request, "question2.html")


def question3(request):
    return render(request, "question3.html")


def question21(request):
    return render(request, "question21.html")


def question22(request):
    return render(request, "question22.html")


def question23(request):
    return render(request, "question23.html")


def question31(request):
    return render(request, "question31.html")


def question32(request):
    return render(request, "question32.html")


def question33(request):
    return render(request, "question33.html")


def result(request):
    return render(request, "result.html")


def level_select(request, category=None):
    if category is None:
        return redirect("category_select")
    levels = [1, 2, 3]
    return render(
        request,
        "level_select.html",
        {"category": category, "levels": levels},
    )

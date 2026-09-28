import logging

from cloudinary.exceptions import Error as CloudinaryError
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from .forms import RegistrationForm, UserProfileForm


logger = logging.getLogger(__name__)


def index(request):
    return render(request, "index.html")


def knowledge(request):
    return render(request, "knowledge.html")


def news(request):
    return render(request, "news.html")


def quiz(request):
    return redirect("category_select")


def community(request):
    return render(request, "community.html")


def physiological_knowledge(request):
    return render(request, "knowledge/physiological_knowledge.html")


def psychological_knowledge(request):
    return render(request, "knowledge/psychological_knowledge.html")


def safety_knowledge(request):
    return render(request, "knowledge/safety_knowledge.html")


def quiz_history(request):
    return render(request, "quiz_history.html")


def category_select(request):
    return render(request, "category_select.html")


def favorite_news(request):
    return render(request, "favorite_news.html")


def login_register(request):
    form_type = request.GET.get("form_type", "login")
    form = None

    if request.method == "POST":
        if form_type == "login":
            username = request.POST.get("username")
            password = request.POST.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                logger.info("User %s logged in successfully.", username)
                messages.success(request, "登录成功！")
                return redirect("index")
            messages.error(request, "用户名或密码错误，请重试。")
            logger.warning("Failed login attempt for user %s.", username)
        else:
            form = RegistrationForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "注册成功，请登录。")
                return redirect("login_register")
            messages.error(request, "注册失败，请检查输入信息。")
    elif form_type == "register":
        form = RegistrationForm()

    return render(
        request,
        "login_register.html",
        {"form_type": form_type, "form": form},
    )


def user_logout(request):
    logout(request)
    messages.success(request, "退出登录成功！")
    return redirect("index")


@login_required(login_url="login_register")
def profile(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
            except CloudinaryError:
                request.user.refresh_from_db()
                form = UserProfileForm(request.POST, instance=request.user)
                form.add_error(
                    "profile_picture",
                    "头像上传失败，请稍后重试。",
                )
                return render(request, "profile.html", {"form": form})
            messages.success(request, "个人信息更新成功！")
            return redirect("profile")
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, "profile.html", {"form": form})

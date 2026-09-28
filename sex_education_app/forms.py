from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class RegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'password1', 'password2']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'age', 'gender', 'phone_number', 'profile_picture']
        help_texts = {
            'username': '必填项。最多 150 个字符。只能包含字母、数字和 @/./+/-/_。',
            'password1': '请输入一个安全的密码。',
            'password2': '请再次输入相同的密码以确认。'
        }
# movies/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model
from .models import Movie, Showtime


User = get_user_model()

class LoginForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={"class":"form-control","placeholder":"you@example.com"}))

User = get_user_model()

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Enter email"})
    )

    full_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Full name"})
    )

    class Meta:
        model = User
        fields = ("full_name", "email", "password1", "password2")

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'})
    )

class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = "__all__"

class ShowtimeForm(forms.ModelForm):
    class Meta:
        model = Showtime
        fields = "__all__"
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type":"datetime-local","class":"form-control"})
        }

class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your email"
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your password"
        })
    )
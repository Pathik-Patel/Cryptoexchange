from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from myapp.models import Profile


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(required=True, label='Username',
                               help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
                               widget=forms.TextInput(attrs={'class': 'form-control'}))

    email = forms.EmailField(required=True, label='Email', help_text='Required. Enter a valid email address.',
                             widget=forms.TextInput(attrs={'class': 'form-control'}))

    password1 = forms.CharField(required=True, label='Password', help_text='Required. Enter a valid password.',
                                widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    password2 = forms.CharField(required=True, label='Password confirmation',
                                help_text='Enter the same password as before, for verification.',
                                widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

from django.contrib.auth.forms import PasswordChangeForm

class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(required=True, label='Old password',
                                   widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password1 = forms.CharField(required=True, label='New password',
                                    widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(required=True, label='Confirm new password',
                                    widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class ProfileForm(forms.ModelForm):
    id_photo = forms.ImageField(required=True, label='ID Photo')

    class Meta:
        model = Profile
        fields = ['id_photo']

class EditProfileForm(forms.ModelForm):
    username = forms.CharField(required=True, label='Username',
                               help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
                               widget=forms.TextInput(attrs={'class': 'form-control'}))

    email = forms.EmailField(required=True, label='Email', help_text='Required. Enter a valid email address.',
                             widget=forms.TextInput(attrs={'class': 'form-control'}))

    id_photo = forms.ImageField(required=False, label='ID Photo')  # Make this field optional

    class Meta:
        model = User
        fields = ['username', 'email', 'id_photo']


class AddMoneyForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2)


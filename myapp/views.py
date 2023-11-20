from decimal import Decimal

import shortuuid
from django.shortcuts import render, get_object_or_404
import requests
from django.contrib import auth, messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import redirect, render
from django.template.defaultfilters import slugify
from django.utils.http import urlsafe_base64_decode

from .forms import CustomUserCreationForm, ProfileForm, EditProfileForm, CustomPasswordChangeForm, AddMoneyForm
from .models import Cryptocurrency, Portfolio, Profile, Referal, Transaction
from .coingeko import get_crypto_price

def generate_referral_code():
    return shortuuid.ShortUUID().random(length=10)
def signup_view(request):
    # check if user is already logged in
    if request.user.is_authenticated:
        return redirect('portfolio')

    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        profile_form = ProfileForm(request.POST, request.FILES)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.password = make_password(user_form.cleaned_data['password1'])
            user.email = user_form.cleaned_data['email']
            user.save()
            profile = profile_form.save(commit=False)
            profile = Profile.objects.create(
                user=user,
                referral_code=generate_referral_code(),
                id_photo=request.FILES['id_photo']
            )
            profile.save()
            messages.success(request, 'You have successfully signed up!', extra_tags='success')
            return redirect('login')
    else:
        user_form = CustomUserCreationForm()
        profile_form = ProfileForm()
    return render(request, 'signup.html', {'user_form': user_form, 'profile_form': profile_form})


# block access to signup page if user is already logged in
def signup_with_referrer_view(request, referral_code):
    # check if user is already logged in
    if request.user.is_authenticated:
        return redirect('portfolio')

    try:
        # get the User Profile of the referrer
        referrer = User.objects.get(profile__referral_code=referral_code)
    except User.DoesNotExist:
        # show error message if referrer does not exist
        return HttpResponse("Referrer does not exist")

    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        profile_form = ProfileForm(request.POST, request.FILES)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.password = make_password(user_form.cleaned_data['password1'])
            user.email = user_form.cleaned_data['email']
            user.save()
            profile = profile_form.save(commit=False)
            profile = Profile.objects.create(
                user=user,
                referral_code=generate_referral_code(),
                id_photo=request.FILES['id_photo']
            )
            profile.save()

            # create a referral instance
            referral = Referal.objects.create(user=user, referrer=referrer)
            referral.save()

            if referrer is not None:
                referrer.profile.bonus += 100  # add referral bonus to referrer
                referrer.profile.save()
                messages.success(request,
                                 f'{referrer.username} recieved a bonus of 100 points from you because you signed up using their referral link!')

            messages.success(request, 'You have successfully signed up!')
            return redirect('login')
    else:
        user_form = CustomUserCreationForm()
        profile_form = ProfileForm()

    return render(request, 'signup.html', {'user_form': user_form, 'profile_form': profile_form, 'referrer': referrer})


def login_view(request):
    # check if user is already logged in
    if request.user.is_authenticated:
        print('before')
        return redirect('portfolio')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=raw_password)
            if user is not None:
                login(request, user)
                request.session['user_id']=user.email
                #print(request.session.get('user_id'),"here i am")
                return redirect('portfolio')
        else:
            messages.error(request, "Invalid username or password.", extra_tags='danger')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


@login_required(login_url="login")
def logout_view(request):
    logout(request)
    messages.success(request, 'You have successfully logged out!')
    request.session.flush()
    return redirect('home')


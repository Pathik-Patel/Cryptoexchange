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

@login_required(login_url="login")
def logout_view(request):
    logout(request)
    messages.success(request, 'You have successfully logged out!')
    request.session.flush()
    return redirect('home')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('portfolio')
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, 'edit_profile.html', {'form': form})
@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            return redirect('portfolio')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})




@login_required
def add_money(request):
    if request.method == 'POST':
        form = AddMoneyForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data.get('amount')
            request.user.profile.balance += amount
            request.user.profile.save()
            return redirect('portfolio')
    else:
        form = AddMoneyForm()
    return render(request, 'add_money.html', {'form': form})



###search page which can be accessed via looking up a cryptocurrency in the home page search box at the top
@login_required(login_url="login")
def add_to_portfolio_view(request):
    if request.method != 'POST':
        return HttpResponse(
            'Need a crypto currency to add to your portfolio. Go back to the home page and search for a crypto currency.')

    # get values from the form
    coin_id = request.POST.get('id')
    quantity = request.POST.get('quantity')
    print(coin_id)

    # get the crypto currency data from the coingecko api based on the coin id
    api_url = f'https://api.coingecko.com/api/v3/coins/{coin_id}'
    response = requests.get(api_url)
    data = response.json()
    print(data)
    # store the name, symbol, current price, and market cap rank of the crypto currency
    user = request.user
    name = data['name']
    id_from_api = data['id']
    symbol = data['symbol']
    current_price = data['market_data']['current_price']['usd']

    try:
        # save the crypto currency to the database
        crypto_currency = Cryptocurrency.objects.create(
            user=user,
            name=name,
            id_from_api=id_from_api,
            symbol=symbol,
            quantity=quantity,
            current_price=current_price,
        )
    except IntegrityError:
        crypto_currency = Cryptocurrency.objects.get(user=user, name=name)
        crypto_currency.quantity += int(quantity)

    crypto_currency.save()

    # calculate the total value of the crypto currency
    total_value = int(quantity) * int(current_price)

    # save the total value of the crypto currency to the database in the portfolio model
    # check if the user already has a portfolio
    if Portfolio.objects.filter(user=user).exists():
        portfolio = Portfolio.objects.get(user=user)
        portfolio.total_value += total_value
    else:
        portfolio = Portfolio(user=user, total_value=total_value)

    portfolio.save()
    messages.success(request, f'{name} has been added to your portfolio.')

    # if all the above steps are successful, redirect the user to the portfolio page
    return redirect('portfolio')

###wallet

@login_required(login_url="login")
def portfolio_view(request):
    # get the current logged in user
    current_user = request.user

    # get the referal code of the current user
    referral_code = current_user.profile.referral_code

    # get a list of all users who have the current user as their referrer
    referrals = Referal.objects.filter(referrer=current_user)

    # get total bonus earned by the current user
    total_bonus = current_user.profile.bonus

    # get the list of cryptocurrencies owned by the current user
    user_cryptocurrencies = Cryptocurrency.objects.filter(user=current_user)

    # fetch live prices for each cryptocurrency
    live_prices = {}
    for crypto in user_cryptocurrencies:
        # fetch live price
        live_price = get_crypto_price(crypto.id_from_api, 'usd')

        # update current price in the database
        crypto.current_price = live_price
        crypto.save()

        live_prices[crypto.id] = live_price

    if user_portfolio := Portfolio.objects.filter(user=current_user).first():
        portfolio = Portfolio.objects.get(user=current_user)
        print("nilay")

        # get all the crypto currencies in the portfolio and recalculate the total value of the portfolio
        new_portfolio_value = 0

        user_cryptocurrencies = Cryptocurrency.objects.filter(user=current_user)
        for cryptocurrency in user_cryptocurrencies:
            # fetch live price
            live_price = live_prices[cryptocurrency.id]
            total_value = float(cryptocurrency.quantity) * live_price
            new_portfolio_value += total_value

        portfolio.total_value = new_portfolio_value
        portfolio.save()

        print(live_prices)
        context = {
            'current_user': current_user,
            'referral_code': referral_code,
            'user_cryptocurrencies': user_cryptocurrencies,
            'user_portfolio': user_portfolio,
            'referrals': referrals,
            'total_bonus': total_bonus,
            'new_portfolio_value': new_portfolio_value,
            'live_prices': live_prices,

        }
    else:
        context = {
            'current_user': current_user,
            'referral_code': referral_code,
            'user_cryptocurrencies': user_cryptocurrencies,
            'user_portfolio': user_portfolio,
            'referrals': referrals,
            'total_bonus': total_bonus,
            'live_prices': live_prices,
        }

    return render(request, 'portfolio.html', context)


@login_required(login_url="login")
def delete_from_portfolio_view(request, pk):
    # get the current logged in user
    user = request.user

    # get the crypto currency object from the database
    crypto_currency = Cryptocurrency.objects.get(pk=pk)

    # delete the crypto currency from the database
    crypto_currency.delete()

    # update the total value of the portfolio
    portfolio = Portfolio.objects.get(user=user)

    # get all the crypto currencies in the portfolio and recalculate the total value of the portfolio
    user_cryptocurrencies = Cryptocurrency.objects.filter(user=user)
    for cryptocurrency in user_cryptocurrencies:
        total_value = cryptocurrency.quantity * cryptocurrency.current_price
        portfolio.total_value += total_value

    portfolio.save()

    # send an alert to the user that the crypto currency has been deleted from the portfolio
    messages.warning(request, f'{crypto_currency.name} has been deleted from your portfolio.')

    return redirect('portfolio')


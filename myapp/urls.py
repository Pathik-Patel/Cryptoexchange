from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home_view, name="home"),

    # user authentication
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path('change_password/', views.change_password, name='change_password'),
    path('change_password/', views.change_password, name='change_password'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path("portfolio/", views.portfolio_view, name="portfolio"),
    path("signup/", views.signup_view, name="signup"),
    path("search/", views.search_view, name="search"),
    path("add_to_portfolio/", views.add_to_portfolio_view, name="add_to_portfolio"),
    path('delete_from_portfolio/<int:pk>/', views.delete_from_portfolio_view, name='delete_from_portfolio'),
    path('buy_crypto/', views.buy_crypto, name='buy_crypto'),
    path('sell_crypto/<int:pk>/', views.sell_crypto, name='sell_crypto'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name="reset/password_reset.html"),
         name='password_reset'),

    path('password_reset_done/',
         auth_views.PasswordResetDoneView.as_view(template_name="reset/password_reset_done.html"),
         name='password_reset_done'),

    path('password_reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='reset/password_reset_confirm.html'), name='password_reset_confirm'),

    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='reset/password_reset_complete.html'), name='password_reset_complete'),

]

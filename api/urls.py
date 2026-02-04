from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path("register/", UserRegistrationAPIView.as_view(), name="register-user"),
    path("login/", UserLoginAPIView.as_view(), name="login-user"),
    path("logout/", UserLogoutAPIView.as_view(), name="logout-user"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("user/", UserInfoAPIView.as_view(), name="user-info"),
    path("products/", views.getProducts, name="products"),
    path("product/<str:pk>/", views.getProduct, name="product"),
    path("cart/", views.GetCart.as_view(), name="cart"),
    path("add-cart/<str:pk>/", views.GetCart.as_view(), name="add-to-cart"),
    path("delete-cart/<str:pk>/", views.GetCart.as_view(), name="delete-cart"),
    path("users/", views.GetUsers.as_view(), name="users"),
    path("current-user/", views.CurrentUserView.as_view(), name="current-user"),
    path('create-order/', views.CreateOrderFromCart.as_view(), name='create-order'),
    path('orders/', views.CreateOrderFromCart.as_view(), name='orders'),
    path("order-items/<str:pk>/", views.getOrderItems, name="order-items"),
]

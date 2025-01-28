from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='index'),
    path('login/', views.login_view, name='login'), # Home page
]

"""
URL configuration for joinbackend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from todolist.views import (
    LoginView,
    RegisterView,
    LogoutView,
    TodoViewSet,
    CategoryViewSet,
    ContactViewSet,
    LoggedUserView
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path('user-info/', LoggedUserView.as_view(), name='logged-user-info'),
    path("signup/", RegisterView.as_view(), name="signup"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("tasks/", TodoViewSet.as_view({"get": "list"}), name="tasks"),
    path("add-task/", TodoViewSet.as_view({"post": "create"}), name="add-task"),
    path("categories/", CategoryViewSet.as_view({"get": "list"}), name="category-list"),
    path("contacts/", ContactViewSet.as_view({"get": "list"}), name="contact-list"),
]

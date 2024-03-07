from todolist.views import sentry_test_view
from django.contrib import admin
from django.views.generic import TemplateView
from rest_framework_nested.routers import NestedSimpleRouter
from rest_framework_nested import routers
from django.urls import path, include, re_path
from django.conf.urls.static import static
from django.conf import settings
from rest_framework.routers import DefaultRouter
from todolist.views import (
    LoginView,
    RegisterView,
    LogoutView,
    TodoViewSet,
    CategoryViewSet,
    ContactViewSet,
    LoggedUserView,
    SubtaskViewSet,
    GuestLoginView
)


router = DefaultRouter()
router.register(r'tasks', TodoViewSet, basename='task')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'contacts', ContactViewSet, basename='contact')

tasks_router = routers.NestedSimpleRouter(router, r'tasks', lookup='task')
tasks_router.register(r'subtasks', SubtaskViewSet, basename='subtask')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/password_reset/', include('django_rest_passwordreset.urls')),
    path('login/', LoginView.as_view(), name='login'),
    path('guest-login/', GuestLoginView.as_view(), name='guest-login'),
    path('user-info/', LoggedUserView.as_view(), name='logged-user-info'),
    path('signup/', RegisterView.as_view(), name='signup'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', include(router.urls)),  
    path('', include(tasks_router.urls)),  
    path('sentry-test/', sentry_test_view, name='sentry_test'),
] 
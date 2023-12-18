from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from django.contrib.auth.models import User
from .serializers import UserSerializer

class RegisterViewTests(TestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.user_data = {
            'username': ''
        }

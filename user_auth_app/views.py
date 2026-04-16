from django.contrib.auth.models import User
from rest_framework import generics, permissions

from .serializers import RegistrationSerializer


class RegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.AllowAny]

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import User
from .serializers import UserProfileSerializer, UserRegistrationSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class UserSearchView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        query = self.request.query_params.get('q', '')
        if not query:
            return User.objects.none()
        return User.objects.filter(
            username__icontains=query
        ).exclude(
            id=self.request.user.id
        )[:5]
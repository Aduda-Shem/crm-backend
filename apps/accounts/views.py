from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.serializers import Serializer, CharField, EmailField, ChoiceField
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


class RegisterSerializer(Serializer):
    username = CharField(max_length=150)
    email = EmailField()
    password = CharField(write_only=True)
    role = ChoiceField(choices=[('MANAGER', 'Manager'), ('AGENT', 'Agent')])


class RegisterAPIView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if User.objects.filter(username=data['username']).exists():
            return Response({'detail': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
        user = User(username=data['username'], email=data['email'], role=data['role'])
        user.set_password(data['password'])
        user.is_active = True
        user.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Registration successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        }, status=status.HTTP_201_CREATED)



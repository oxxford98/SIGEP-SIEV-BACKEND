from rest_framework.views import APIView
from users.models import User
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from users.api.serializers import LoginSerializer, RegisterSerializer
from django.utils import timezone


class UserApiViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = LoginSerializer
    queryset = User.objects.all()

    def get_permissions(self):
        # Registro público; /me para cualquier sesión; gestionar usuarios solo is_staff.
        if self.action == 'create':
            self.permission_classes = [AllowAny,]
        elif self.action == 'me':
            self.permission_classes = [IsAuthenticated,]
        else:
            self.permission_classes = [IsAdminUser,]
        return super(self.__class__, self).get_permissions()

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Datos del usuario autenticado por el token JWT."""
        return Response(LoginSerializer(request.user).data)

    def create(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            data = {
                'id': serializer.data['id'],
                'username': serializer.data['username'],
                'email': serializer.data['email'],
            }
            return Response(data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        serializer = LoginSerializer(
            User.objects.filter(deleted_at=None), many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        try:
            if serializer.validated_data['password'] is not None:
                instance.set_password(serializer.validated_data['password'])
                instance.save()
        except KeyError:
            pass
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.deleted_at = timezone.now()
        user.is_active = False  # un usuario borrado no puede volver a obtener tokens
        user.save()
        serializer = LoginSerializer(user)
        data = {
            'status': 'ok',

        }
        return Response(data=data)


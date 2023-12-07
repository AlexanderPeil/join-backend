from django.shortcuts import get_object_or_404, render
from .serializers import (
    TodoSerializer,
    UserSerializer,
    CategorySerializer,
    SubtaskSerializer,
    ContactSerializer,
    TodoDetailSerializer
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.contrib.auth.models import User
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import permissions
from rest_framework.authtoken.models import Token
from .models import Todo, Category, Contact, Subtask


class GuestLoginView(APIView):
    def post(self, request):
        guest_username = 'guest'

        try:
            guest_user = User.objects.get(username=guest_username)
        except User.DoesNotExist:
            guest_user = User.objects.create_user(username=guest_username, password='guest_password')

        token, created = Token.objects.get_or_create(user=guest_user)

        return Response({
            "token": token.key,
            "user_id": guest_user.pk,
            "email": guest_user.email
        })


class ReadOnlyGuestPermission(permissions.BasePermission):
    """
    Berechtigungsklasse, die nur Lesezugriff für Gastbenutzer erlaubt.
    """

    def has_permission(self, request, view):
        if request.user.username == 'guest':
            return request.method in permissions.SAFE_METHODS
        return True


class TodoViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, ReadOnlyGuestPermission]
    serializer_class = TodoSerializer

    def get_queryset(self):
        return Todo.objects.filter(user=self.request.user).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = TodoDetailSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        todo = get_object_or_404(Todo, pk=kwargs['pk'], user=request.user)
        serializer = TodoDetailSerializer(todo, context={'request': request})
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if instance.user != request.user:
            return Response(
                {"detail": "You do not have permission to edit this task."},
                status=status.HTTP_403_FORBIDDEN,
            )

        non_nested_data = {key: value for key, value in request.data.items() if key not in ['category', 'assigned_to', 'subtasks']}
        serializer = self.get_serializer(instance, data=non_nested_data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if 'category' in request.data:
            category_id = request.data['category']
            instance.category = Category.objects.get(id=category_id)
        
        if 'assigned_to' in request.data:
            instance.assigned_to.clear()
            for contact_id in request.data['assigned_to']:
                contact = Contact.objects.get(id=contact_id)
                instance.assigned_to.add(contact)

        instance.save()  

        return Response(serializer.data)


    def perform_update(self, serializer):
        serializer.save()



    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response(
                {"detail": "You have no permission to delete this task."},
                status=status.HTTP_403_FORBIDDEN,
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, ReadOnlyGuestPermission]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()

    def get_queryset(self): 
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ContactViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, ReadOnlyGuestPermission]
    serializer_class = ContactSerializer
    queryset = Contact.objects.all()

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        if instance.user != request.user:
            return Response(
                {"detail": "You have no permission to edit this task."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    

class SubtaskViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, ReadOnlyGuestPermission]
    serializer_class = SubtaskSerializer
    queryset = Subtask.objects.all()

    def get_queryset(self):
        task_id = self.kwargs.get('task_pk')
        if task_id is not None:
            return Subtask.objects.filter(todo__id=task_id)  
        return super().get_queryset()
    

    def create(self, request, *args, **kwargs):
        task_id = self.kwargs.get('task_pk')
        if task_id is None:
            return Response({"detail": "Task ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        subtasks_data = request.data
        if not isinstance(subtasks_data, list):
            subtasks_data = [subtasks_data]  

        created_subtasks = []
        for subtask_data in subtasks_data:
            subtask_data['todo'] = task_id
            subtask_data['user'] = request.user.id
            serializer = self.get_serializer(data=subtask_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            created_subtasks.append(serializer.data)

        return Response(created_subtasks, status=status.HTTP_201_CREATED)


    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)



class RegisterView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if User.objects.filter(email=request.data["email"]).exists():
            return Response(
                {"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST
            )
        if serializer.is_valid():
            user = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(ObtainAuthToken):
    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user_id": user.pk, "email": user.email})


class LogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_200_OK)
    

class LoggedUserView(APIView):
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
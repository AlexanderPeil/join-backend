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
from rest_framework.authtoken.models import Token
from .models import Todo, Category, Contact, Subtask


class TodoViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
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


    # def create(self, request, *args, **kwargs):
    #     serializer = TodoSerializer(data=request.data, context={'request': request})
    #     if serializer.is_valid():
    #         serializer.save(user=request.user)

    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     else:
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if instance.user != request.user:
            return Response(
                {"detail": "You do not have permission to edit this task."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Aktualisieren Sie nur die nicht-verschachtelten Felder mit dem Serializer
        non_nested_data = {key: value for key, value in request.data.items() if key not in ['category', 'assigned_to', 'subtasks']}
        serializer = self.get_serializer(instance, data=non_nested_data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Aktualisieren Sie verschachtelte Felder manuell
        if 'category' in request.data:
            # Aktualisieren Sie die Kategorie
            category_id = request.data['category']
            instance.category = Category.objects.get(id=category_id)
        
        if 'assigned_to' in request.data:
            # Aktualisieren Sie die zugewiesenen Kontakte
            instance.assigned_to.clear()
            for contact_id in request.data['assigned_to']:
                contact = Contact.objects.get(id=contact_id)
                instance.assigned_to.add(contact)

        instance.save()  # Speichern Sie die Instanz nach den manuellen Änderungen

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
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()


class ContactViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ContactSerializer
    queryset = Contact.objects.all()

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

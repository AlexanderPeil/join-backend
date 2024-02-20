from random import randint
import uuid
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
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


class GuestLoginView(APIView):
    """
    API view for guest user login.

    This view handles the creation or retrieval of a guest user and generates an
    authentication token for the guest session. It is intended to provide limited access
    or functionality to users who haven't registered or logged in with a personal account.

    Methods:
    - post: Handles the POST request to create or retrieve a guest user. It checks if a
      user with the username 'guest' exists. If not, it creates a new user with this
      username and a predefined password. Then, it retrieves or creates a token for
      this guest user and returns the token key, user id, and email in the response.

    Note:
    - The password for the guest user is hardcoded, which may not be secure. For a
      production environment, consider implementing a more secure method of handling
      guest user authentication.
    - This implementation assumes a simplistic guest user setup. Depending on the
      application's requirements, you might need a more sophisticated approach.
    """
    def post(self, request):
        random_number = randint(1000, 9999)  
        guest_username = f'guest_{random_number}'

        guest_user = User.objects.create_user(username=guest_username, password=uuid.uuid4().hex)
        token, created = Token.objects.get_or_create(user=guest_user)

        return Response({
            "token": token.key,
            "user_id": guest_user.pk,
            "email": guest_user.email
        })


class TodoViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling Todo instances.

    This ViewSet provides 'list', 'create', 'retrieve', 'update', and 'delete' actions for Todo instances.
    It uses TokenAuthentication and custom permissions to ensure that only authenticated users
    can modify data, and guest users have read-only access.

    Authentication and Permissions:
    - Authentication: TokenAuthentication is used to authenticate users.
    - Permissions: IsAuthenticated is applied for permission checks.

    Serializer Class:
    - TodoSerializer is used for serialization and deserialization of Todo instances.

    Overridden Methods:
    - get_queryset: Filters the Todo instances by the current user and orders them by creation date.
    - list: Lists all Todo instances for the current user.
    - retrieve: Retrieves a specific Todo instance. Returns 404 if not found or not owned by the user.
    - update: Updates a Todo instance. Custom logic is included for handling nested relationships.
      Returns a 403 Forbidden response if the user is not the owner of the Todo.
    - destroy: Deletes a Todo instance. Returns a 403 Forbidden response if the user is not the owner.

    Note:
    - The custom logic in 'update' method ensures that only the owner of a Todo can modify it
      and handles updating nested relationships like 'category' and 'assigned_to'.
    - In 'destroy' method, it's ensured that only the owner of a Todo can delete it.
    """
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

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

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

        subtasks_data = request.data.get('subtasks', [])
        for subtask_data in subtasks_data:
            subtask_id = subtask_data.get('id')
            if not subtask_id:
                Subtask.objects.create(todo=instance, user=request.user, **subtask_data)


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
    """
    ViewSet for handling Category instances.

    This ViewSet provides the standard 'list', 'create', 'retrieve', 'update', and 'delete'
    actions for Category instances. It is configured to allow only authenticated users
    to modify data, and guest users are given read-only access.

    Authentication and Permissions:
    - Authentication: Uses TokenAuthentication to authenticate users.
    - Permissions: Applies IsAuthenticated to ensure proper access control.

    Serializer Class:
    - Uses CategorySerializer for serialization and deserialization of Category instances.

    Methods:
    - get_queryset: Overrides the default queryset to return categories belonging to the current user.
    - perform_create: Overrides the default create behavior to set the 'user' field to the current user.

    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()

    def get_queryset(self): 
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling Contact instances.

    This ViewSet offers 'list', 'create', 'retrieve', 'update', and 'delete' actions for Contact instances.
    It employs token-based authentication and custom permissions to ensure secure access control, allowing
    only authenticated users to modify data, while guest users have read-only access.

    Authentication and Permissions:
    - Authentication: Uses TokenAuthentication for user authentication.
    - Permissions: IsAuthenticated is used to control access.

    Serializer Class:
    - Utilizes ContactSerializer for serialization and deserialization of Contact instances.

    Methods:
    - get_queryset: Overrides to return contacts associated with the current authenticated user.
    - perform_create: Overrides to assign the newly created contact to the current user.
    - update: Custom update method. Ensures that only the owner of the contact can edit it.
      If the user is not the owner, a 403 Forbidden response is returned.

    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
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
    """
    ViewSet for handling Subtask instances.

    This ViewSet provides the standard actions ('list', 'create', 'retrieve', 'update', 
    'delete') for Subtask instances. It includes custom logic for filtering subtasks 
    by tasks and handling batch creation of subtasks.

    Authentication and Permissions:
    - Authentication: Uses TokenAuthentication for authenticating users.
    - Permissions: IsAuthenticated is applied for access control.

    Serializer Class:
    - Utilizes SubtaskSerializer for serialization and deserialization of Subtask instances.

    Methods:
    - get_queryset: Overrides to return subtasks related to a specific task, identified by 'task_pk'.
    - create: Custom creation method allowing for the creation of one or more subtasks. 
      Requires 'task_pk' to associate the new subtasks with a specific task.
    - partial_update: Inherits the default behavior for partial updates of subtask instances.

    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
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
    """
    API view for user registration.

    This view handles the creation of new user accounts. It does not require any authentication
    or permissions as it's intended for users who are not yet registered.

    Authentication and Permissions:
    - Authentication: None. This view is accessible without any authentication.
    - Permissions: None. This view does not require any permissions, allowing access to any visitor.

    Methods:
    - post: Handles POST requests for user registration. It uses the UserSerializer to validate
      and create new user accounts. It checks if an account with the provided email already exists
      and if not, proceeds to create a new user. Returns a 400 Bad Request response if the email
      already exists or if the data is invalid.

    """
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if User.objects.filter(email=request.data["email"]).exists():
            return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        token, created  = Token.objects.get_or_create(user=user)
        
        data = {
            "user": serializer.data, 
            "token": token.key
        }
        return Response(data, status=status.HTTP_201_CREATED)

        
class LoginView(ObtainAuthToken):
    """
    API view for user login.

    This view extends Django Rest Framework's ObtainAuthToken to provide token-based authentication
    for users. It handles the login process, validating user credentials and returning an authentication
    token along with user details.

    Methods:
    - post: Handles POST requests for user login. It uses the ObtainAuthToken's serializer to validate
      user credentials. Upon successful validation, it retrieves or creates a new authentication token
      for the user and returns this token along with the user's ID and email.

    """
    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created  = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user_id": user.pk, "email": user.email})


class LogoutView(APIView):
    """
    API view for user logout.

    This view handles the logout process by invalidating the user's authentication token.
    It requires the user to be authenticated with a valid token to access this endpoint.

    Authentication and Permissions:
    - Authentication: Uses TokenAuthentication to authenticate users.
    - Permissions: IsAuthenticated to ensure only authenticated users can access this view.

    Methods:
    - post: Handles POST requests for user logout. It deletes the user's auth token,
      effectively logging them out of the system. Returns a 200 OK status on successful logout.

    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_200_OK)
    

class LoggedUserView(APIView):
    """
    API view for retrieving the currently logged-in user's details.

    This view is used to obtain information about the user that is currently authenticated. 
    It supports both Basic and Token authentication methods.

    Authentication and Permissions:
    - Authentication: Supports both BasicAuthentication and TokenAuthentication.
    - Permissions: IsAuthenticated to ensure only authenticated users can access this view.

    Methods:
    - get: Handles GET requests. It serializes the currently authenticated user's data
      using the UserSerializer and returns this data in the response.

    """
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
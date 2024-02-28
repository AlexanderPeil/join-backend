from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Todo, Category, Contact, Subtask
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.

    This serializer is used for creating and retrieving user instances. It includes fields
    for the user's id, username, first name, last name, email, and password. The password
    is write-only to ensure it's not exposed through the API.

    Fields:
    - id (ReadOnlyField): The unique id of the user.
    - username (CharField): The username of the user.
    - first_name (CharField): The first name of the user.
    - last_name (CharField): The last name of the user.
    - email (EmailField): The email address of the user.
    - password (CharField): The password for the user account. This field is write-only.

    Overridden Methods:
    - create: Handles creating a new User instance along with a corresponding Contact
      instance. The password is set and hashed, and the user's contact information is
      added to the Contact model.
    """
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            email=validated_data["email"],
        )
        user.set_password(validated_data["password"])
        user.save()

        Contact.objects.create(
            firstname=validated_data.get("first_name", ""),
            lastname=validated_data.get("last_name", ""),
            email=validated_data["email"],
            user=user,
        )
        return user


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the Category model.

    This serializer is used for handling serialization and deserialization of Category
    instances. It includes the 'name' and 'color' fields for input/output, and the 'id'
    field which is read-only.
    
    """
    class Meta:
        model = Category
        fields = ["name", "color", "id"]
        read_only_fields = ["id"]


class SubtaskSerializer(serializers.ModelSerializer):
    """
    Serializer for the Subtask model.

    This serializer is used for handling serialization and deserialization of Subtask
    instances. It includes all fields from the Subtask model. The 'todo' and 'user'
    fields are marked as not required, allowing for more flexibility in API usage.
    
    """
    class Meta:
        model = Subtask
        fields = "__all__"
        extra_kwargs = {'todo': {'required': False}, 'user': {'required': False}}


class ContactSerializer(serializers.ModelSerializer):
    """
    Serializer for the Contact model.

    This serializer is used for handling the serialization and deserialization of Contact
    instances. It includes fields for the contact's id, firstname, lastname, email, phone,
    and color. The 'id' field is read-only, ensuring it is not editable through the API.
    
    """
    class Meta:
        model = Contact
        fields = ["id", "firstname", "lastname", "email", "phone", "color"]
        read_only_fields = ["id"]


class TodoSerializer(serializers.ModelSerializer):
    """
    Serializer for the Todo model.

    This serializer handles serialization and deserialization of Todo instances.
    It includes custom fields for 'user', 'category', 'assigned_to', and 'subtasks'.
    The 'user' field is read-only and automatically set to the current user.
    The 'category' and 'assigned_to' fields are represented by their primary keys.
    The 'subtasks' field uses SubtaskSerializer for nested serialization.

    Overridden Methods:
    - create: Handles the creation of a new Todo instance along with its related subtasks.
      The current user is automatically set as the user of the todo and its subtasks.
      The 'assigned_to' and 'subtasks' fields are handled separately to manage the many-to-many
      and nested relationships, respectively.
    
    """
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=Contact.objects.all(), many=True)
    subtasks = SubtaskSerializer(many=True, required=False)


    class Meta:
        model = Todo
        fields = "__all__"

    def create(self, validated_data):
        assigned_to_data = validated_data.pop('assigned_to', [])
        subtasks_data = validated_data.pop('subtasks', [])

        user = self.context['request'].user
        todo = Todo.objects.create(user=user, **validated_data)

        todo.assigned_to.set(assigned_to_data)

        for subtask_data in subtasks_data:
            Subtask.objects.create(todo=todo, user=user, **subtask_data)

        return todo


class TodoDetailSerializer(serializers.ModelSerializer):
    """
    API view for resetting a user's password.

    This view handles the password reset functionality. It allows users to reset their password by providing a valid token received via email (or other means). The process ensures that only users with valid reset tokens can change their password, enhancing security.

    Authentication and Permissions:
    - Authentication: None required for accessing this view, as it's meant for users who cannot log in due to a forgotten password.
    - Permissions: None required, as the action does not access any user-specific data that requires authentication.

    Methods:
    - post: Handles POST requests. It expects a payload containing 'email', 'token', and 'password' fields. The method validates the provided data, checks the reset token's validity, and if valid, resets the user's password to the new value. Responses vary based on the operation outcome:
        - Success: Returns a response with a message indicating the password has been successfully reset.
        - Invalid Token: Returns a 400 Bad Request response if the token is invalid.
        - User Not Found: Returns a 404 Not Found response if no user is associated with the provided email.
        - Validation Errors: Returns a 400 Bad Request response containing the serializer errors if the request data is invalid.

    Usage:
    To reset a password, send a POST request to this view with a payload containing the user's email, the reset token, and the new password. Ensure the token is valid and associated with the user's email.
    """
    category = CategorySerializer(read_only=True)
    assigned_to = ContactSerializer(many=True, read_only=True)
    subtasks = SubtaskSerializer(many=True, read_only=True)

    class Meta:
        model = Todo
        fields = '__all__'


class ResetPasswordSerializer(serializers.Serializer):
    """
    Serializer for password reset data.

    This serializer is used to validate and deserialize the data required for resetting a user's password. It ensures that the necessary fields are included in the request and that they meet the validation criteria set forth for a password reset operation.

    Fields:
    - token: A CharField that represents the password reset token. This token is typically sent to the user's email address and is required to validate the password reset request. It ensures that the request is authorized.
    - password: A CharField that represents the new password for the user. This field is used to update the user's password once the token is validated and the request is deemed legitimate.

    Validation:
    The serializer performs basic validation to ensure that both fields are provided and are not empty. Further validation, such as token validity and password strength, should be handled externally (e.g., in the view).

    Usage:
    This serializer is intended to be used in password reset views or endpoints where users submit their reset tokens and new passwords. It simplifies the process of validating and deserializing input data, ensuring that only valid and complete requests are processed.
    """
    token = serializers.CharField()
    password = serializers.CharField()
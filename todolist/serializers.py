from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Todo, Category, Contact, Subtask


class UserSerializer(serializers.ModelSerializer):
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
    class Meta:
        model = Category
        fields = ["name", "color", "id"]
        read_only_fields = ["id"]


class SubtaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtask
        fields = "__all__"
        extra_kwargs = {"todo": {"read_only": True}, "user": {"read_only": True}}


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ["id", "firstname", "lastname", "email", "phone", "color"]
        read_only_fields = ["id"]


class TodoSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=Contact.objects.all(), many=True)
    subtasks = serializers.PrimaryKeyRelatedField(queryset=Subtask.objects.all(), many=True)


    class Meta:
        model = Todo
        fields = "__all__"
        # fields = ['id', 'title', 'description', 'status', 'created_at', 'user', 'category', 'priority', 'due_date', 'assigned_to', 'subtasks']
        # read_only_fields = ['user', 'created_at']


class TodoDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    assigned_to = ContactSerializer(many=True, read_only=True)
    subtasks = SubtaskSerializer(many=True, read_only=True)

    class Meta:
        model = Todo
        fields = '__all__'


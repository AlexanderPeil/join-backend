from django.db import models
from datetime import date
from django.conf import settings


class Category(models.Model):
    """
    Represents a category for organizing todos.
    
    """
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f'({self.id}) {self.name}'


class Contact(models.Model):
    """
    Represents a contact in the system.

    """
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    phone = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=7, default='#FFFFFF')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f'({self.id}) {self.firstname} {self.lastname}'


class Todo(models.Model):
    """
    Represents a todo item in the system.

    """

    TODO_STATUS = [
    ('todo', 'Todo'),
    ('awaiting_feedback', 'Awaiting Feedback'),
    ('in_progress', 'In Progress'),
    ('done', 'Done'),
    ]

    PRIORITIES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('urgent', 'Urgent'),
    ]

    created_at = models.DateField(default=date.today)
    due_date = models.DateField(default=date.today)
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=300)
    status = models.CharField(max_length=20, choices=TODO_STATUS, default='todo')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITIES, default='medium')
    assigned_to = models.ManyToManyField(Contact, related_name='todos_assigned')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f'({self.id}) {self.title}'


class Subtask(models.Model):
    """
        
    Represents a subtask of a Todo item in the system.

    """
    title = models.CharField(max_length=100)
    checked = models.BooleanField(default=False)
    todo = models.ForeignKey(Todo, on_delete=models.CASCADE, related_name='subtasks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f'({self.id}) {self.title}'
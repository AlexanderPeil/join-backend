from django.contrib import admin
from todolist.models import Todo, Category, Contact, Subtask

admin.site.register(Todo)
admin.site.register(Category)
admin.site.register(Contact)
admin.site.register(Subtask)
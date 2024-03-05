from django.contrib.auth.models import User
from .models import Category, Contact, Todo
from datetime import date

def create_predefined_content_for_guest(user):
    categories_info = [
    {"name": "Development", "color": "#9d00ff"},
    {"name": "Bugfixing", "color": "#ff0d00"},
    {"name": "Meeting", "color": "#0400ff"},
    ]

    categories = {category_info["name"]: Category.objects.create(user=user, **category_info) for category_info in categories_info}

    contacts = [
        {"firstname": "Alexander", 
         "lastname": "Peil", 
         "email": "Alex@web.de",
         "phone": "+4915733333333", 
         "color": "#9485ed"},

        {"firstname": "Sandra", 
         "lastname": "Westermann", 
         "email": "Sandy@dev.com", 
         "phone": "+4915734444444", 
         "color": "#31a30f"},

         {"firstname": "Peter",
          "lastname": "Meier",
          "email": "Pete@gmail.com",
          "phone": "+491537856",
          "color": "#ad1d25"}
    ]

    contacts_models = [Contact.objects.create(user=user, **contact) for contact in contacts]

    tasks = [
        {"due_date": date.today(), 
         "title": "Fixing bug",
           "description": "We have to fix the bugs.", 
           "status": "todo", 
           "priority": "urgent",
           "category_name": "Bugfixing"},

        {"due_date": date.today(), 
         "title": "Waiting for feedback",
           "description": "Please check the new feature. We need a feedback until the end of the week.", 
           "status": "awaiting_feedback", 
           "priority": "medium",
           "category_name": "Development"},

        {"due_date": date.today(), 
         "title": "Check the coffe machine",
           "description": "The coffee machine is broken. If we don't fix it as fast as we can our whole team won't work productively anymore.", 
           "status": "in_progress", 
           "priority": "urgent",
           "category_name": "Bugfixing"},

        {"due_date": date.today(), 
         "title": "Team meeting",
           "description": "We have an unscheduled meeting. The whole team will be present", 
           "status": "done", 
           "priority": "low",
           "category_name": "Meeting"},
    ]

    for task_info in tasks:
        category_name = task_info.pop("category_name")  
        category = categories[category_name]  
        task = Todo.objects.create(user=user, category=category, **task_info)
        task.assigned_to.set(contacts_models)


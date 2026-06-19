from django.contrib import admin
from .models import Client, Project, Worker, Task, Material, Expense, UserProfile, ProjectUpdate

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone']
    list_filter = ['role']

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email']
    search_fields = ['name', 'phone']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'client', 'status', 'budget', 'start_date']
    list_filter = ['status', 'project_type']
    search_fields = ['name', 'location']

@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'phone', 'daily_wage', 'is_active']
    list_filter = ['is_active', 'role']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'worker', 'status', 'priority', 'deadline']
    list_filter = ['status', 'priority']

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'quantity', 'unit', 'unit_price']

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'amount', 'category', 'date']
    list_filter = ['category']

@admin.register(ProjectUpdate)
class ProjectUpdateAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'created_at', 'created_by']

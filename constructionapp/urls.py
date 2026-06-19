from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # [VULN] Vulnerable login replaces Django's default
    path('accounts/login-vuln/', views.vulnerable_login, name='vulnerable_login'),

    # [VULN - BROKEN AUTH] Self role escalation endpoint
    

    # ===== ADMIN PANEL =====
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/clients/', views.admin_client_list, name='admin_client_list'),
    path('admin-panel/clients/add/', views.admin_client_add, name='admin_client_add'),
    path('admin-panel/clients/delete/<int:pk>/', views.admin_client_delete, name='admin_client_delete'),
    path('admin-panel/projects/', views.admin_project_list, name='admin_project_list'),
    path('admin-panel/projects/add/', views.admin_project_add, name='admin_project_add'),
    path('admin-panel/projects/<int:pk>/', views.admin_project_detail, name='admin_project_detail'),
    path('admin-panel/projects/edit/<int:pk>/', views.admin_project_edit, name='admin_project_edit'),

    # [VULN - CSRF] Delete via GET — no POST required
    path('admin-panel/projects/delete/<int:pk>/', views.admin_project_delete, name='admin_project_delete'),

    path('admin-panel/workers/', views.admin_worker_list, name='admin_worker_list'),
    path('admin-panel/workers/add/', views.admin_worker_add, name='admin_worker_add'),
    path('admin-panel/workers/delete/<int:pk>/', views.admin_worker_delete, name='admin_worker_delete'),
    path('admin-panel/projects/<int:project_pk>/tasks/add/', views.admin_task_add, name='admin_task_add'),
    path('admin-panel/tasks/delete/<int:pk>/', views.admin_task_delete, name='admin_task_delete'),
    path('admin-panel/projects/<int:project_pk>/expenses/add/', views.admin_expense_add, name='admin_expense_add'),
    path('admin-panel/expenses/delete/<int:pk>/', views.admin_expense_delete, name='admin_expense_delete'),
    path('admin-panel/projects/<int:project_pk>/materials/add/', views.admin_material_add, name='admin_material_add'),
    path('admin-panel/materials/delete/<int:pk>/', views.admin_material_delete, name='admin_material_delete'),
    path('admin-panel/projects/<int:project_pk>/updates/add/', views.admin_update_add, name='admin_update_add'),

    # ===== USER (CLIENT) PANEL =====
    path('my-projects/', views.user_dashboard, name='user_dashboard'),
    path('my-projects/profile/', views.user_profile, name='user_profile'),

    # [VULN - IDOR] No ownership check
    path('my-projects/<int:pk>/', views.user_project_detail, name='user_project_detail'),

    # [VULN - XSS #3] Search endpoint
    path('search/', views.user_search, name='user_search'),
]

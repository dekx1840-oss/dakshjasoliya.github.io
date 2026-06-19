from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from functools import wraps
from .models import Client, Project, Worker, Task, Material, Expense, UserProfile, ProjectUpdate
# =============================================
# HELPER: Get user role safely
# =============================================
def get_user_role(user):
    try:
        return user.userprofile.role
    except Exception:
        return 'user'
# =============================================
# DECORATOR: Admin only
# =============================================
def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if get_user_role(request.user) != 'admin' and not request.user.is_superuser:
            return render(request, 'constructionapp/access_denied.html', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper
# =============================================
# HOME - redirect based on role
# =============================================
@login_required
def home(request):
    if request.user.is_superuser or get_user_role(request.user) == 'admin':
        return redirect('admin_dashboard')
    return redirect('user_dashboard')
# =============================================
# ADMIN VIEWS
# =============================================
@admin_required
def admin_dashboard(request):
    context = {
        'total_projects': Project.objects.count(),
        'total_clients': Client.objects.count(),
        'total_workers': Worker.objects.count(),
        'ongoing': Project.objects.filter(status='ongoing').count(),
        'completed': Project.objects.filter(status='completed').count(),
        'planning': Project.objects.filter(status='planning').count(),
        'pending_tasks': Task.objects.filter(status='pending').count(),
        'total_users': User.objects.count(),
        'recent_projects': Project.objects.order_by('-id')[:6],
        'recent_expenses': Expense.objects.order_by('-date')[:5],
    }
    return render(request, 'constructionapp/admin/dashboard.html', context)
@admin_required
def admin_client_list(request):
    clients = Client.objects.all().order_by('-id')
    return render(request, 'constructionapp/admin/client_list.html', {'clients': clients})
@admin_required
def admin_client_add(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        name = request.POST.get('name', '').strip()
        if not username or not password or not name:
            messages.error(request, 'Name, username and password are required!')
            return redirect('admin_client_add')
        if User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" already exists!')
            return redirect('admin_client_add')
        user = User.objects.create_user(
            username=username, password=password,
            email=request.POST.get('email', ''),
            first_name=name
        )
        UserProfile.objects.get_or_create(user=user, defaults={'role': 'user'})
        client = Client.objects.create(
            user=user, name=name,
            phone=request.POST.get('phone', ''),
            email=request.POST.get('email', ''),
            address=request.POST.get('address', '')
        )
        messages.success(request, f'Client "{client.name}" added with login account!')
        return redirect('admin_client_list')
    return render(request, 'constructionapp/admin/client_form.html')
@admin_required
def admin_client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    name = client.name
    if client.user:
        client.user.delete()
    else:
        client.delete()
    messages.success(request, f'Client "{name}" deleted!')
    return redirect('admin_client_list')
@admin_required
def admin_project_list(request):
    projects = Project.objects.all().order_by('-id')
    return render(request, 'constructionapp/admin/project_list.html', {'projects': projects})
@admin_required
def admin_project_add(request):
    if request.method == 'POST':
        try:
            project = Project(
                client=Client.objects.get(pk=request.POST['client']),
                name=request.POST.get('name', ''),
                project_type=request.POST.get('project_type', 'residential'),
                location=request.POST.get('location', ''),
                floors=request.POST.get('floors', 1) or 1,
                start_date=request.POST['start_date'],
                budget=request.POST.get('budget', 0),
                status=request.POST.get('status', 'planning'),
                description=request.POST.get('description', '')
            )
            area = request.POST.get('area_sqft', '')
            if area:
                project.area_sqft = float(area)
            end_date = request.POST.get('end_date', '')
            if end_date:
                project.end_date = end_date
            if request.FILES.get('site_image'):
                project.site_image = request.FILES['site_image']
            if request.FILES.get('floor_plan'):
                project.floor_plan = request.FILES['floor_plan']
            if request.FILES.get('elevation_image'):
                project.elevation_image = request.FILES['elevation_image']
            project.save()
            messages.success(request, 'Project added successfully!')
            return redirect('admin_project_list')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    return render(request, 'constructionapp/admin/project_form.html', {
        'clients': Client.objects.all(), 'action': 'Add'
    })
@admin_required
def admin_project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        try:
            project.client = Client.objects.get(pk=request.POST['client'])
            project.name = request.POST.get('name', project.name)
            project.project_type = request.POST.get('project_type', project.project_type)
            project.location = request.POST.get('location', project.location)
            project.floors = request.POST.get('floors', project.floors) or 1
            project.start_date = request.POST['start_date']
            project.budget = request.POST.get('budget', project.budget)
            project.status = request.POST.get('status', project.status)
            project.description = request.POST.get('description', project.description)
            area = request.POST.get('area_sqft', '')
            if area:
                project.area_sqft = float(area)
            end_date = request.POST.get('end_date', '')
            if end_date:
                project.end_date = end_date
            if request.FILES.get('site_image'):
                project.site_image = request.FILES['site_image']
            if request.FILES.get('floor_plan'):
                project.floor_plan = request.FILES['floor_plan']
            if request.FILES.get('elevation_image'):
                project.elevation_image = request.FILES['elevation_image']
            project.save()
            messages.success(request, 'Project updated!')
            return redirect('admin_project_detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    return render(request, 'constructionapp/admin/project_form.html', {
        'project': project, 'clients': Client.objects.all(), 'action': 'Edit'
    })
@admin_required
def admin_project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    context = {
        'project': project,
        'tasks': project.task_set.all().order_by('-id'),
        'materials': project.material_set.all(),
        'expenses': project.expense_set.all().order_by('-date'),
        'updates': project.projectupdate_set.all().order_by('-created_at'),
        'total_expense': project.total_expenses(),
        'budget_remaining': project.budget_remaining(),
        'progress': project.progress_percent(),
    }
    return render(request, 'constructionapp/admin/project_detail.html', context)
@admin_required
def admin_project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    project.delete()
    messages.success(request, 'Project deleted!')
    return redirect('admin_project_list')
@admin_required
def admin_worker_list(request):
    workers = Worker.objects.all().order_by('-id')
    return render(request, 'constructionapp/admin/worker_list.html', {'workers': workers})
@admin_required
def admin_worker_add(request):
    if request.method == 'POST':
        try:
            w = Worker(
                name=request.POST.get('name', ''),
                phone=request.POST.get('phone', ''),
                role=request.POST.get('role', ''),
                daily_wage=request.POST.get('daily_wage', 0),
                joining_date=request.POST['joining_date']
            )
            if request.FILES.get('photo'):
                w.photo = request.FILES['photo']
            w.save()
            messages.success(request, 'Worker added!')
            return redirect('admin_worker_list')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    return render(request, 'constructionapp/admin/worker_form.html')
@admin_required
def admin_worker_delete(request, pk):
    worker = get_object_or_404(Worker, pk=pk)
    worker.delete()
    messages.success(request, 'Worker deleted!')
    return redirect('admin_worker_list')
@admin_required
def admin_task_add(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if request.method == 'POST':
        try:
            worker_id = request.POST.get('worker', '')
            worker = None
            if worker_id:
                worker = Worker.objects.get(pk=worker_id)
            Task.objects.create(
                project=project,
                title=request.POST.get('title', ''),
                worker=worker,
                deadline=request.POST['deadline'],
                status=request.POST.get('status', 'pending'),
                priority=request.POST.get('priority', 'medium'),
                description=request.POST.get('description', '')
            )
            messages.success(request, 'Task added!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('admin_project_detail', pk=project_pk)
    return render(request, 'constructionapp/admin/task_form.html', {
        'project': project, 'workers': Worker.objects.filter(is_active=True)
    })
@admin_required
def admin_task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    project_pk = task.project.pk
    task.delete()
    messages.success(request, 'Task deleted!')
    return redirect('admin_project_detail', pk=project_pk)
@admin_required
def admin_expense_add(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if request.method == 'POST':
        try:
            e = Expense(
                project=project,
                title=request.POST.get('title', ''),
                amount=request.POST.get('amount', 0),
                date=request.POST['date'],
                category=request.POST.get('category', 'other'),
                note=request.POST.get('note', '')
            )
            if request.FILES.get('receipt'):
                e.receipt = request.FILES['receipt']
            e.save()
            messages.success(request, 'Expense added!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('admin_project_detail', pk=project_pk)
    return render(request, 'constructionapp/admin/expense_form.html', {'project': project})
@admin_required
def admin_expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    project_pk = expense.project.pk
    expense.delete()
    messages.success(request, 'Expense deleted!')
    return redirect('admin_project_detail', pk=project_pk)
@admin_required
def admin_material_add(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if request.method == 'POST':
        try:
            Material.objects.create(
                project=project,
                name=request.POST.get('name', ''),
                quantity=float(request.POST.get('quantity', 0)),
                unit=request.POST.get('unit', ''),
                unit_price=request.POST.get('unit_price', 0),
                stock_alert=float(request.POST.get('stock_alert', 10))
            )
            messages.success(request, 'Material added!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('admin_project_detail', pk=project_pk)
    return render(request, 'constructionapp/admin/material_form.html', {'project': project})
@admin_required
def admin_material_delete(request, pk):
    material = get_object_or_404(Material, pk=pk)
    project_pk = material.project.pk
    material.delete()
    messages.success(request, 'Material deleted!')
    return redirect('admin_project_detail', pk=project_pk)
@admin_required
def admin_update_add(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if request.method == 'POST':
        try:
            u = ProjectUpdate(
                project=project,
                title=request.POST.get('title', ''),
                description=request.POST.get('description', ''),
                created_by=request.user
            )
            if request.FILES.get('image'):
                u.image = request.FILES['image']
            u.save()
            messages.success(request, 'Update posted!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('admin_project_detail', pk=project_pk)
    return render(request, 'constructionapp/admin/update_form.html', {'project': project})
# =============================================
# USER (CLIENT) VIEWS
# =============================================
@login_required
def user_profile(request):
    if request.user.is_superuser or get_user_role(request.user) == 'admin':
        return redirect('admin_dashboard')
    try:
        client = Client.objects.get(user=request.user)
        projects = Project.objects.filter(client=client)
        context = {
            'client': client,
            'total_projects': projects.count(),
            'ongoing': projects.filter(status='ongoing').count(),
            'completed': projects.filter(status='completed').count(),
        }
    except Client.DoesNotExist:
        context = {'client': None}
    return render(request, 'constructionapp/user/profile.html', context)
@login_required
def user_dashboard(request):
    if request.user.is_superuser or get_user_role(request.user) == 'admin':
        return redirect('admin_dashboard')
    try:
        client = Client.objects.get(user=request.user)
        projects = Project.objects.filter(client=client)
        context = {
            'client': client,
            'projects': projects,
            'total_projects': projects.count(),
            'ongoing': projects.filter(status='ongoing').count(),
            'completed': projects.filter(status='completed').count(),
        }
    except Client.DoesNotExist:
        context = {'client': None, 'projects': []}
    return render(request, 'constructionapp/user/dashboard.html', context)
@login_required
def user_project_detail(request, pk):
    if request.user.is_superuser or get_user_role(request.user) == 'admin':
        return redirect('admin_project_detail', pk=pk)
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        return render(request, 'constructionapp/access_denied.html')
    project = get_object_or_404(Project, pk=pk, client=client)
    context = {
        'project': project,
        'tasks': project.task_set.all().order_by('-id'),
        'materials': project.material_set.all(),
        'expenses': project.expense_set.all().order_by('-date'),
        'updates': project.projectupdate_set.all().order_by('-created_at'),
        'total_expense': project.total_expenses(),
        'budget_remaining': project.budget_remaining(),
        'progress': project.progress_percent(),
    }
    return render(request, 'constructionapp/user/project_detail.html', context)
def custom_logout(request):
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')
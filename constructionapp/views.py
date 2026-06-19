from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout as auth_logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.utils.safestring import mark_safe
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
# [VULN - BROKEN AUTH #1] Role check only on 'admin' string —
# any user can set their role manually via /set-role/ endpoint
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
    if request.user.is_superuser:
        return redirect('admin_dashboard')

    return redirect('user_dashboard')

# =============================================
# [VULN - BROKEN AUTH #2] No brute-force protection
# No rate limiting, no lockout after failed attempts
# Try: admin/admin, admin/password, admin/123456 etc.
# =============================================
@csrf_exempt  # [VULN - CSRF #1] Login form has no CSRF protection
def vulnerable_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')

        # [VULN - SQL INJECTION #1] Raw SQL with direct string concatenation
        # Payload: username = ' OR '1'='1' --
        # Payload: username = admin'--
        with connection.cursor() as cursor:
            query = "SELECT id, username FROM auth_user WHERE username='" + username + "' AND password='" + password + "'"
            try:
                cursor.execute(query)
                row = cursor.fetchone()
            except Exception:
                row = None

        # Still use Django auth for actual session (SQLi only leaks data here)
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            # [VULN - USER ENUMERATION] Different message for wrong user vs wrong password
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Incorrect password for this user.')
            else:
                messages.error(request, 'Username does not exist.')
            return render(request, 'constructionapp/login.html')
    return render(request, 'constructionapp/login.html')

# =============================================
# [VULN - BROKEN AUTH #3] Anyone can promote themselves to admin
# GET /set-role/?role=admin  → instant privilege escalation
# =============================================
# =============================================
# ADMIN VIEWS
# =============================================
@admin_required
def admin_dashboard(request):

    if not request.user.is_superuser:
        return redirect('user_dashboard')

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

# =============================================
# [VULN - SQL INJECTION #2] Client search with raw query
# URL: /admin-panel/clients/?search=' OR '1'='1
# Payload: ' UNION SELECT id,username,password,email,username FROM auth_user--
# =============================================
@admin_required
def admin_client_list(request):
    search = request.GET.get('search', '')
    if search:
        with connection.cursor() as cursor:
            # Vulnerable raw query — no parameterization
            cursor.execute("SELECT id, name, phone, email FROM constructionapp_client WHERE name LIKE '%" + search + "%'")
            rows = cursor.fetchall()
        clients = [{'id': r[0], 'name': r[1], 'phone': r[2], 'email': r[3]} for r in rows]
        return render(request, 'constructionapp/admin/client_list.html', {'clients': clients, 'search': search, 'raw_results': True})
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
        messages.success(request, f'Client "{client.name}" added!')
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

# =============================================
# [VULN - UNRESTRICTED FILE UPLOAD]
# No file type check, no extension whitelist
# Upload a .php or .py webshell directly
# Uploaded files stored in /media/ — publicly accessible
# Try uploading: shell.php, evil.html (with JS), malicious.svg
# =============================================
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
            # [VULN] No validation on file type or size
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

    # [VULN - XSS #1] Project name rendered without escaping in context
    # If project name contains <script>alert(1)</script> it will execute
    # (needs |safe filter in template — see project_detail.html)
    context = {
        'project': project,
        'project_name_raw': mark_safe(project.name),  # Intentionally unsafe
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
    # [VULN - CSRF #2] Delete via GET request — no POST/CSRF token required
    # Attacker can send: <img src="http://localhost:8000/admin-panel/projects/delete/1/">
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
            # [VULN] No file type check on worker photo
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

# =============================================
# [VULN - IDOR] No ownership check on project pk
# User A can access User B's project just by changing the ID in URL
# /my-projects/1/  →  /my-projects/2/  →  /my-projects/3/ etc.
# =============================================
@login_required
def user_project_detail(request, pk):
    if request.user.is_superuser or get_user_role(request.user) == 'admin':
        return redirect('admin_project_detail', pk=pk)

    # [VULN - IDOR] Removed client=client filter — any logged-in user can view any project
    project = get_object_or_404(Project, pk=pk)

    # [VULN - XSS #2] Reflected XSS via 'msg' GET parameter
    # URL: /my-projects/1/?msg=<script>alert(document.cookie)</script>
    raw_msg = request.GET.get('msg', '')

    context = {
        'project': project,
        'xss_msg': mark_safe(raw_msg),  # Intentionally unsafe — reflected XSS
        'tasks': project.task_set.all().order_by('-id'),
        'materials': project.material_set.all(),
        'expenses': project.expense_set.all().order_by('-date'),
        'updates': project.projectupdate_set.all().order_by('-created_at'),
        'total_expense': project.total_expenses(),
        'budget_remaining': project.budget_remaining(),
        'progress': project.progress_percent(),
    }
    return render(request, 'constructionapp/user/project_detail.html', context)

# =============================================
# [VULN - XSS #3] Stored XSS via worker search
# Search for: <script>alert('XSS')</script>
# Result rendered unescaped back on page
# =============================================
@login_required
def user_search(request):
    query = request.GET.get('q', '')
    results = []
    if query:
        results = Worker.objects.filter(name__icontains=query)
    # [VULN] query reflected directly into template without escaping
    return render(request, 'constructionapp/user/search.html', {
        'query': mark_safe(query),
        'results': results
    })

def custom_logout(request):
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')

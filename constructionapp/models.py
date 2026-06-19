from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'Client/User'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    def is_admin(self):
        return self.role == 'admin'

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Project(models.Model):
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    ]
    TYPE_CHOICES = [
        ('residential', 'Residential House'),
        ('commercial', 'Commercial Office'),
        ('apartment', 'Apartment'),
        ('villa', 'Villa'),
        ('renovation', 'Renovation'),
        ('other', 'Other'),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    project_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='residential')
    location = models.CharField(max_length=300)
    area_sqft = models.FloatField(null=True, blank=True)
    floors = models.IntegerField(default=1)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    description = models.TextField(blank=True)
    # Architecture plan images
    site_image = models.ImageField(upload_to='projects/site/', blank=True, null=True)
    floor_plan = models.ImageField(upload_to='projects/plans/', blank=True, null=True)
    elevation_image = models.ImageField(upload_to='projects/elevation/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def total_expenses(self):
        return sum(e.amount for e in self.expense_set.all())

    def budget_remaining(self):
        return self.budget - self.total_expenses()

    def progress_percent(self):
        total = self.task_set.count()
        if total == 0:
            return 0
        done = self.task_set.filter(status='completed').count()
        return int((done / total) * 100)

class Worker(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    role = models.CharField(max_length=100)
    daily_wage = models.DecimalField(max_digits=8, decimal_places=2)
    joining_date = models.DateField()
    photo = models.ImageField(upload_to='workers/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    worker = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    deadline = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Material(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    quantity = models.FloatField()
    unit = models.CharField(max_length=50)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_alert = models.FloatField(default=10)

    def __str__(self):
        return self.name

    def total_cost(self):
        return round(self.quantity * float(self.unit_price), 2)

    def is_low_stock(self):
        return self.quantity <= self.stock_alert

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('material', 'Material'),
        ('labor', 'Labor'),
        ('equipment', 'Equipment'),
        ('transport', 'Transport'),
        ('other', 'Other'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    note = models.TextField(blank=True)
    receipt = models.ImageField(upload_to='receipts/', blank=True, null=True)

    def __str__(self):
        return self.title

class ProjectUpdate(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='updates/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.title

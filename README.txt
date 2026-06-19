╔══════════════════════════════════════════════════════════╗
║     CONSTRUCTPRO — CONSTRUCTION MANAGEMENT SYSTEM        ║
║           Real World Project — Final Version             ║
╚══════════════════════════════════════════════════════════╝

📁 FOLDER STRUCTURE:
─────────────────────
constructionproject/
├── manage.py
├── README.txt
├── constructionproject/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── constructionapp/
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── admin.py
    ├── apps.py
    ├── signals.py
    └── templates/
        └── constructionapp/
            ├── login.html
            ├── access_denied.html
            ├── admin/         ← Admin panel templates
            └── user/          ← Client portal templates


🚀 HOW TO RUN:
──────────────
STEP 1 — Open CMD in this folder (where manage.py is):
         The folder should show manage.py when you type: dir

STEP 2 — Install packages (run once):
         pip install django django-crispy-forms crispy-bootstrap4 Pillow

STEP 3 — Setup database:
         python manage.py makemigrations
         python manage.py migrate

STEP 4 — Create ADMIN account:
         python manage.py createsuperuser
         (Enter username, email, password)

STEP 5 — Make superuser an Admin role:
         python manage.py shell
         >>> from constructionapp.models import UserProfile
         >>> from django.contrib.auth.models import User
         >>> u = User.objects.get(username='YOUR_USERNAME')
         >>> p, _ = UserProfile.objects.get_or_create(user=u)
         >>> p.role = 'admin'
         >>> p.save()
         >>> exit()

STEP 6 — Run server:
         python manage.py runserver

STEP 7 — Open browser:
         http://127.0.0.1:8000/


👥 TWO SEPARATE PANELS:
────────────────────────
ADMIN LOGIN  → Goes to /admin-panel/ (full access)
CLIENT LOGIN → Goes to /my-projects/ (view only their projects)

To add a client with login:
  → Login as admin
  → Go to Clients → Add Client
  → Fill name, phone, email, address
  → Set username & password for client login
  → Client can now login and see their project


✨ FEATURES:
────────────
✅ Separate Admin & Client panels
✅ Admin: Full CRUD for all modules
✅ Client: View-only their own projects
✅ Upload Site Photo, Floor Plan, Elevation Drawing
✅ Worker photos
✅ Expense receipts
✅ Project progress tracking (%)
✅ Budget vs expense tracking
✅ Material low stock alerts
✅ Project updates with progress photos
✅ Task assignment with priority & status
✅ Bootstrap 5 professional design


🔐 ACCESS CONTROL:
───────────────────
Admin panel URL: /admin-panel/
Client portal URL: /my-projects/
Django admin URL: /admin/

Clients CANNOT access admin panel
Admin can access everything

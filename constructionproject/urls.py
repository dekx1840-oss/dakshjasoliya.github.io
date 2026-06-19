from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from constructionapp.views import custom_logout

# Customize admin site
admin.site.site_header = "ConstructPro Admin"
admin.site.site_title = "ConstructPro Admin Portal"
admin.site.index_title = "Welcome to ConstructPro Administration"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('constructionapp.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='constructionapp/login.html'), name='login'),
    path('accounts/logout/', custom_logout, name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

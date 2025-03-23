from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def home_redirect(request):
    if request.user.is_student():
        return redirect('accounts:student_dashboard')
    elif request.user.is_lecturer():
        return redirect('accounts:lecturer_dashboard')
    else:
        return redirect('admin:index')

urlpatterns = [
    path('', home_redirect, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('schools/', include('schools.urls')),
    path('courses/', include('courses.urls')),
    path('assignments/', include('assignments.urls')),
]

# Custom error handlers
handler404 = 'core.views.custom_404'
handler500 = 'core.views.custom_500'

# Configure admin site
admin.site.site_header = 'University Management System'
admin.site.site_title = 'UMS Admin Portal'
admin.site.index_title = 'Administration'

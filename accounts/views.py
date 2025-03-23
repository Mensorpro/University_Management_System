from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.utils import timezone
from .forms import UserRegistrationForm, CustomAuthenticationForm, ProfileEditForm
from courses.models import Course, Enrollment
from assignments.models import Assignment, Submission

class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'
    
    def get_success_url(self):
        if self.request.user.is_student():
            return reverse_lazy('accounts:student_dashboard')
        elif self.request.user.is_lecturer():
            return reverse_lazy('accounts:lecturer_dashboard')
        return reverse_lazy('admin:index')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to the University Management System.')
            if user.is_student():
                return redirect('accounts:student_dashboard')
            else:
                return redirect('accounts:lecturer_dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    recent_submissions = None
    if request.user.is_student():
        recent_submissions = Submission.objects.filter(
            student=request.user
        ).select_related(
            'assignment', 'assignment__course'
        ).order_by('-submitted_at')[:5]
    
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'recent_submissions': recent_submissions
    })

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})

@login_required
def student_dashboard(request):
    if not request.user.is_student():
        messages.error(request, 'Access denied. Students only.')
        return redirect('home')
    
    enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related('course', 'course__lecturer', 'course__department')
    
    pending_assignments = Assignment.objects.filter(
        course__enrollments__student=request.user,
        due_date__gt=timezone.now()
    ).exclude(
        submissions__student=request.user
    ).select_related('course').order_by('due_date')
    
    recent_submissions = Submission.objects.filter(
        student=request.user
    ).select_related('assignment', 'assignment__course').order_by('-submitted_at')[:5]
    
    context = {
        'enrollments': enrollments,
        'pending_assignments': pending_assignments,
        'recent_submissions': recent_submissions,
    }
    return render(request, 'accounts/student_dashboard.html', context)

@login_required
def lecturer_dashboard(request):
    if not request.user.is_lecturer():
        messages.error(request, 'Access denied. Lecturers only.')
        return redirect('home')
    
    courses = Course.objects.filter(
        lecturer=request.user
    ).select_related('department')
    
    recent_submissions = Submission.objects.filter(
        assignment__course__lecturer=request.user,
        status='submitted'
    ).select_related(
        'student', 'assignment', 'assignment__course'
    ).order_by('-submitted_at')[:10]
    
    context = {
        'courses': courses,
        'recent_submissions': recent_submissions,
    }
    return render(request, 'accounts/lecturer_dashboard.html', context)

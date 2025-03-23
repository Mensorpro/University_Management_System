from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.urls import reverse
from .forms import UserRegistrationForm, CustomAuthenticationForm, ProfileEditForm
from courses.models import Course
from assignments.models import Assignment, Submission

class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'

    def get_success_url(self):
        if self.request.user.is_student():
            return reverse('accounts:student_dashboard')
        else:
            return reverse('accounts:lecturer_dashboard')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('accounts:login')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {'user': request.user})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})

@login_required
def student_dashboard(request):
    if not request.user.is_student():
        messages.error(request, 'Access denied. Students only.')
        return redirect('home')
    
    enrollments = request.user.enrollments.select_related(
        'course',
        'course__lecturer',
        'course__department'
    )
    
    # Get upcoming assignments
    upcoming_assignments = Assignment.objects.filter(
        course__enrollments__student=request.user,
        due_date__gt=timezone.now()
    ).order_by('due_date')[:5]
    
    # Get recent submissions
    recent_submissions = request.user.submissions.select_related(
        'assignment',
        'assignment__course'
    ).order_by('-submitted_at')[:5]
    
    context = {
        'enrollments': enrollments,
        'upcoming_assignments': upcoming_assignments,
        'recent_submissions': recent_submissions
    }
    
    return render(request, 'accounts/student_dashboard.html', context)

@login_required
def lecturer_dashboard(request):
    if not request.user.is_lecturer():
        messages.error(request, 'Access denied. Lecturers only.')
        return redirect('home')
    
    # Get all courses taught by the lecturer with submission stats
    courses = Course.objects.filter(
        lecturer=request.user
    ).annotate(
        student_count=Count('enrollments', distinct=True),
        assignment_count=Count('assignments', distinct=True),
        submission_count=Count('assignments__submissions', distinct=True),
        ungraded_count=Count(
            'assignments__submissions',
            filter=Q(assignments__submissions__marks__isnull=True),
            distinct=True
        )
    )
    
    # Get all submissions for the lecturer's courses, ordered by submission date
    recent_submissions = Submission.objects.filter(
        assignment__course__lecturer=request.user
    ).select_related(
        'student',
        'assignment',
        'assignment__course'
    ).order_by(
        '-submitted_at'
    )[:10]
    
    # Calculate overall statistics
    total_students = sum(course.student_count for course in courses)
    total_assignments = sum(course.assignment_count for course in courses)
    total_submissions = sum(course.submission_count for course in courses)
    pending_submissions = sum(course.ungraded_count for course in courses)
    
    context = {
        'courses': courses,
        'recent_submissions': recent_submissions,
        'stats': {
            'total_students': total_students,
            'total_assignments': total_assignments,
            'total_submissions': total_submissions,
            'pending_submissions': pending_submissions
        }
    }
    
    return render(request, 'accounts/lecturer_dashboard.html', context)

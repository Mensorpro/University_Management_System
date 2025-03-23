from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Assignment, Submission
from courses.models import Course
from .forms import AssignmentForm, SubmissionForm, GradingForm

@login_required
def assignment_list(request):
    if request.user.is_student():
        assignments = Assignment.objects.filter(
            course__enrollments__student=request.user
        ).select_related('course')
    else:
        assignments = Assignment.objects.filter(
            course__lecturer=request.user
        ).select_related('course')
    
    return render(request, 'assignments/assignment_list.html', {'assignments': assignments})

@login_required
def assignment_detail(request, pk):
    assignment = get_object_or_404(Assignment.objects.select_related('course', 'created_by'), pk=pk)
    submission = None
    if request.user.is_student():
        submission = Submission.objects.filter(
            assignment=assignment,
            student=request.user
        ).first()
    
    return render(request, 'assignments/assignment_detail.html', {
        'assignment': assignment,
        'submission': submission
    })

@login_required
def create_assignment(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if request.user != course.lecturer:
        messages.error(request, 'Only the course lecturer can create assignments.')
        return redirect('courses:course_detail', pk=course_id)
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.course = course
            assignment.created_by = request.user
            assignment.save()
            messages.success(request, 'Assignment created successfully.')
            return redirect('assignments:assignment_detail', pk=assignment.pk)
    else:
        form = AssignmentForm()
    
    return render(request, 'assignments/assignment_form.html', {
        'form': form,
        'course': course,
        'title': 'Create Assignment'
    })

@login_required
def edit_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    if request.user != assignment.course.lecturer:
        messages.error(request, 'Only the course lecturer can edit assignments.')
        return redirect('assignments:assignment_detail', pk=pk)
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assignment updated successfully.')
            return redirect('assignments:assignment_detail', pk=assignment.pk)
    else:
        form = AssignmentForm(instance=assignment)
    
    return render(request, 'assignments/assignment_form.html', {
        'form': form,
        'assignment': assignment,
        'title': 'Edit Assignment'
    })

@login_required
def delete_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    if request.user != assignment.course.lecturer:
        messages.error(request, 'Only the course lecturer can delete assignments.')
        return redirect('assignments:assignment_detail', pk=pk)
    
    if request.method == 'POST':
        course_id = assignment.course.id
        assignment.delete()
        messages.success(request, 'Assignment deleted successfully.')
        return redirect('courses:course_detail', pk=course_id)
    
    return render(request, 'assignments/assignment_confirm_delete.html', {'assignment': assignment})

@login_required
def submit_assignment(request, pk):
    if not request.user.is_student():
        messages.error(request, 'Only students can submit assignments.')
        return redirect('assignments:assignment_list')
    
    assignment = get_object_or_404(Assignment, pk=pk)
    submission = Submission.objects.filter(assignment=assignment, student=request.user).first()
    
    if request.method == 'POST':
        form = SubmissionForm(request.POST, instance=submission)
        if form.is_valid():
            new_submission = form.save(commit=False)
            new_submission.assignment = assignment
            new_submission.student = request.user
            new_submission.submitted_at = timezone.now()
            new_submission.save()
            messages.success(request, 'Assignment submitted successfully.')
            return redirect('assignments:assignment_detail', pk=pk)
    else:
        form = SubmissionForm(instance=submission)
    
    return render(request, 'assignments/submit_assignment.html', {
        'form': form,
        'assignment': assignment,
        'submission': submission
    })

@login_required
def submission_detail(request, pk):
    submission = get_object_or_404(
        Submission.objects.select_related('assignment', 'student', 'assignment__course'),
        pk=pk
    )
    if request.user != submission.student and request.user != submission.assignment.course.lecturer:
        messages.error(request, 'You do not have permission to view this submission.')
        return redirect('assignments:assignment_list')
    
    return render(request, 'assignments/submission_detail.html', {'submission': submission})

@login_required
def grade_submission(request, pk):
    submission = get_object_or_404(
        Submission.objects.select_related('assignment', 'student', 'assignment__course'),
        pk=pk
    )
    if request.user != submission.assignment.course.lecturer:
        messages.error(request, 'Only the course lecturer can grade submissions.')
        return redirect('assignments:submission_detail', pk=pk)
    
    if request.method == 'POST':
        form = GradingForm(request.POST, instance=submission)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.graded_by = request.user
            submission.graded_at = timezone.now()
            submission.save()
            messages.success(request, 'Submission graded successfully.')
            return redirect('assignments:submission_detail', pk=pk)
    else:
        form = GradingForm(instance=submission)
    
    return render(request, 'assignments/grade_submission.html', {
        'form': form,
        'submission': submission
    })

@login_required
def my_submissions(request):
    if not request.user.is_student():
        messages.error(request, 'Only students can view their submissions.')
        return redirect('assignments:assignment_list')
    
    submissions = Submission.objects.filter(
        student=request.user
    ).select_related('assignment', 'assignment__course').order_by('-submitted_at')
    
    return render(request, 'assignments/my_submissions.html', {'submissions': submissions})

@login_required
def pending_submissions(request):
    if not request.user.is_lecturer():
        messages.error(request, 'Only lecturers can view pending submissions.')
        return redirect('assignments:assignment_list')
    
    submissions = Submission.objects.filter(
        assignment__course__lecturer=request.user,
        status='submitted'
    ).select_related('assignment', 'student', 'assignment__course').order_by('submitted_at')
    
    return render(request, 'assignments/pending_submissions.html', {'submissions': submissions})

from django.contrib import admin
from django.utils import timezone
from .models import Assignment, Submission

class SubmissionInline(admin.TabularInline):
    model = Submission
    extra = 0
    readonly_fields = ('submitted_at', 'is_late')
    raw_id_fields = ('student', 'graded_by')

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'due_date', 'total_marks', 'is_active', 'is_past_due')
    list_filter = ('course__department', 'is_active', 'due_date')
    search_fields = ('title', 'course__code', 'course__name')
    raw_id_fields = ('course', 'created_by')
    inlines = [SubmissionInline]
    
    def is_past_due(self, obj):
        return timezone.now() > obj.due_date
    is_past_due.boolean = True
    is_past_due.short_description = 'Past Due'

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'status', 'marks', 'submitted_at', 'is_late')
    list_filter = ('status', 'assignment__course')
    search_fields = ('student__username', 'assignment__title')
    raw_id_fields = ('student', 'assignment', 'graded_by')
    readonly_fields = ('submitted_at', 'is_late')
    
    def is_late(self, obj):
        return obj.submitted_at > obj.assignment.due_date if obj.submitted_at else False
    is_late.boolean = True
    is_late.short_description = 'Submitted Late'

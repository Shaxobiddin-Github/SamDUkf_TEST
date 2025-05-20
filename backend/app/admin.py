from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, University, Faculty, Student, Test, Question,
    Answer, StudentTest
)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'is_teacher', 'is_student', 'is_staff']
    list_filter = ['is_teacher', 'is_student', 'is_staff']

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('is_teacher', 'is_student')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('is_teacher', 'is_student')}),
    )

# Boshqa modellarga o‘zgartirish shart emas
@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'university']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'student_id', 'faculty']

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'subject', 'created_by', 'start_time', 'end_time']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'test', 'text', 'correct_option']

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'question', 'selected_option', 'is_correct', 'answered_at']

@admin.register(StudentTest)
class StudentTestAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'test', 'is_completed', 'completed_at']

from django.db import models


# core/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser

from django.contrib.auth.models import AbstractUser, Group, Permission

class User(AbstractUser):
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        Group,
        related_name="group",  # related_name o'zgartiring
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="user_permissions",  # related_name o'zgartiring
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )


class University(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Faculty(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=50)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    course = models.CharField(max_length=50, blank=True, null=True)  # New field
    group = models.CharField(max_length=50, blank=True, null=True)   # New field

    def __str__(self):
        return self.user.username

class Test(models.Model):
    title = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)  # Teacher
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    group = models.CharField(max_length=50, blank=True, null=True)  # New field for group assignment

    def __str__(self):
        return self.title

class Question(models.Model):
    test = models.ForeignKey("Test", on_delete=models.CASCADE)
    text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1)  # 'A', 'B', 'C', 'D'

class Answer(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1)
    is_correct = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)







# core/models.py

class StudentTest(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'test')

from django import forms
from .models import User, Student, Faculty

class AddStudentForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    faculty = forms.ModelChoiceField(queryset=Faculty.objects.all())
    course = forms.CharField(max_length=50, required=False)
    group = forms.CharField(max_length=50, required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'faculty', 'course', 'group']

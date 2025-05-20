# core/serializers.py

from rest_framework import serializers
from .models import Test, Question, Answer, Student, Faculty, University

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        exclude = ['correct_option']  # correct answer is hidden initially

class TestListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = ['id', 'title', 'subject', 'start_time', 'end_time']

class TestDetailSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(source='question_set', many=True)
    
    class Meta:
        model = Test
        fields = ['id', 'title', 'subject', 'start_time', 'end_time', 'questions']

class AnswerSubmitSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected_option = serializers.CharField(max_length=1)

class ResultSerializer(serializers.Serializer):
    test_id = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    percentage = serializers.FloatField()
    detailed = serializers.ListField()

# ------------------Foydalanuvchilarni qushish -------------


# core/serializers.py

from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Student

User = get_user_model()

class RegisterStudentSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    faculty_id = serializers.IntegerField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'faculty_id']

    def create(self, validated_data):
        faculty_id = validated_data.pop('faculty_id')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data, is_student=True)
        user.set_password(password)
        user.save()

        Student.objects.create(user=user, faculty_id=faculty_id, student_id=user.username)
        return user

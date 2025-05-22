from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from django.utils import timezone
from django.contrib.auth import get_user_model
import openpyxl
import logging

from .models import StudentTest, Test, Question, Answer, Student
from .serializers import (
    TestListSerializer, TestDetailSerializer, AnswerSubmitSerializer, ResultSerializer, RegisterStudentSerializer
)

logger = logging.getLogger(__name__)
User = get_user_model()

# --------- DRF API VIEWS ---------

class TestListView(generics.ListAPIView):
    queryset = Test.objects.all()
    serializer_class = TestListSerializer
    permission_classes = [IsAuthenticated]

class TestDetailView(generics.RetrieveAPIView):
    queryset = Test.objects.all()
    serializer_class = TestDetailSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        test = self.get_object()
        if test.start_time > timezone.now() or test.end_time < timezone.now():
            return Response({'error': 'Test is not available at this time.'}, status=403)
        return super().get(request, *args, **kwargs)

class SubmitAnswersView(generics.GenericAPIView):
    serializer_class = AnswerSubmitSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        student = Student.objects.get(user=request.user)
        question_ids = []
        correct = 0
        detailed_result = []
        
        for ans_data in request.data.get('answers', []):
            serializer = self.get_serializer(data=ans_data)
            serializer.is_valid(raise_exception=True)
            question = Question.objects.get(id=serializer.validated_data['question_id'])
            selected = serializer.validated_data['selected_option'].upper()
            is_correct = selected == question.correct_option

            Answer.objects.create(
                student=student,
                question=question,
                selected_option=selected,
                is_correct=is_correct
            )
            question_ids.append(question.id)
            correct += 1 if is_correct else 0
            detailed_result.append({
                "question": question.text,
                "selected": selected,
                "correct": question.correct_option,
                "is_correct": is_correct
            })

        total = len(question_ids)
        return Response({
            "test_id": question.test.id,
            "total_questions": total,
            "correct_answers": correct,
            "percentage": round(correct * 100 / total, 2),
            "detailed": detailed_result
        }, status=200)

class UploadQuestionsFromExcelView(generics.GenericAPIView):
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        test_id = request.POST.get('test_id')

        if not file or not test_id:
            return Response({'error': 'Fayl va test_id kerak.'}, status=400)

        try:
            test = Test.objects.get(id=test_id)
        except Test.DoesNotExist:
            return Response({'error': 'Test topilmadi.'}, status=404)

        wb = openpyxl.load_workbook(file)
        sheet = wb.active

        for row in sheet.iter_rows(min_row=2, values_only=True):
            Question.objects.create(
                test=test,
                text=row[0],
                option_a=row[1],
                option_b=row[2],
                option_c=row[3],
                option_d=row[4],
                correct_option=row[5].upper()
            )

        return Response({'success': 'Savollar muvaffaqiyatli yuklandi!'}, status=201)

class RegisterStudentView(generics.CreateAPIView):
    serializer_class = RegisterStudentSerializer
    permission_classes = [IsAuthenticated]  # optional: faqat o‘qituvchilar qo‘sha olsin

    def post(self, request, *args, **kwargs):
        # Optional: faqat teacher foydalanuchi qo‘sha oladi
        if not request.user.is_teacher:
            return Response({'error': 'Faqat o‘qituvchilar talaba qo‘sha oladi.'}, status=403)
        return super().post(request, *args, **kwargs)

class TestStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, test_id):
        if not request.user.is_teacher:
            return Response({'error': 'Faqat o‘qituvchilar kirishi mumkin'}, status=403)

        try:
            test = Test.objects.get(id=test_id, teacher=request.user)
        except Test.DoesNotExist:
            return Response({'error': 'Test topilmadi'}, status=404)

        all_questions = Question.objects.filter(test=test)
        total_questions = all_questions.count()

        answers = Answer.objects.filter(question__in=all_questions).select_related('student', 'question')
        student_stats = {}

        for ans in answers:
            sid = ans.student.id
            if sid not in student_stats:
                student_stats[sid] = {
                    'student_name': f"{ans.student.user.first_name} {ans.student.user.last_name}",
                    'correct': 0,
                    'wrong': 0,
                }
            correct_option = ans.question.correct_option.upper()
            if ans.selected_option.upper() == correct_option:
                student_stats[sid]['correct'] += 1
            else:
                student_stats[sid]['wrong'] += 1

        result = []
        for sid, stat in student_stats.items():
            total = stat['correct'] + stat['wrong']
            result.append({
                'student': stat['student_name'],
                'correct': stat['correct'],
                'wrong': stat['wrong'],
                'score_percent': round((stat['correct'] / total_questions) * 100, 2)
            })

        return Response({'test': test.title, 'total_questions': total_questions, 'results': result})

class StartTestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, test_id):
        try:
            test = Test.objects.get(id=test_id)
        except Test.DoesNotExist:
            return Response({'error': 'Test topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        if test.start_time and now < test.start_time:
            return Response({'error': 'Test hali boshlanmadi'}, status=status.HTTP_403_FORBIDDEN)

        if test.end_time and now > test.end_time:
            return Response({'error': 'Test vaqti tugagan'}, status=status.HTTP_403_FORBIDDEN)

        return Response({'message': 'Test boshlash mumkin'}, status=status.HTTP_200_OK)

class SubmitAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, test_id):
        user = request.user
        try:
            test = Test.objects.get(id=test_id)
        except Test.DoesNotExist:
            return Response({'error': 'Test topilmadi'}, status=404)

        question_id = request.data.get('question_id')
        selected_option = request.data.get('selected_option')

        try:
            question = Question.objects.get(id=question_id, test=test)
        except Question.DoesNotExist:
            return Response({'error': 'Savol topilmadi'}, status=404)

        now = timezone.now()
        if test.start_time and now < test.start_time:
            return Response({'error': 'Test hali boshlanmadi'}, status=403)
        if test.end_time and now > test.end_time:
            return Response({'error': 'Test vaqti tugagan'}, status=403)

        correct = question.correct_option.upper() == selected_option.upper()

        answer, created = Answer.objects.update_or_create(
            student=user.student,
            question=question,
            defaults={'selected_option': selected_option, 'is_correct': correct}
        )

        return Response({'correct': correct})

class FinishTestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, test_id):
        user = request.user
        try:
            test = Test.objects.get(id=test_id)
        except Test.DoesNotExist:
            return Response({'error': 'Test topilmadi'}, status=404)

        if StudentTest.objects.filter(student=user.student, test=test).exists():
            return Response({'error': 'Siz bu testni allaqachon topshirdingiz'}, status=403)

        StudentTest.objects.create(student=user.student, test=test)

        return Response({'message': 'Test muvaffaqiyatli yakunlandi'})

# core/views.py

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from .models import StudentTest, Test, Question, Answer, Student
from .serializers import TestListSerializer, TestDetailSerializer, AnswerSubmitSerializer, ResultSerializer

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
        if test.start_time > now() or test.end_time < now():
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







# --------------EXCEL FILE dan savollarni yuklash-------------------------



# core/views.py davomiga

from rest_framework.parsers import MultiPartParser
import openpyxl
from .models import Test, Question

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



# ------------------Foydalanuvchilarni qushish ----------------------



# core/views.py

from .serializers import RegisterStudentSerializer

class RegisterStudentView(generics.CreateAPIView):
    serializer_class = RegisterStudentSerializer
    permission_classes = [IsAuthenticated]  # optional: faqat o‘qituvchilar qo‘sha olsin

    def post(self, request, *args, **kwargs):
        # Optional: faqat teacher foydalanuvchi qo‘sha oladi
        if not request.user.is_teacher:
            return Response({'error': 'Faqat o‘qituvchilar talaba qo‘sha oladi.'}, status=403)
        return super().post(request, *args, **kwargs)





# -------------------------STATISTIKA------------------------------




# core/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Test, Answer, Question
from django.contrib.auth import get_user_model

User = get_user_model()

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

        # Jadvalga aylantirish
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



# ------------------------TIME-----------------------------




# core/views.py

from django.utils import timezone
from rest_framework import status

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

        # Agar boshlash uchun maxsus logika bo‘lsa, shu yerda yozamiz

        return Response({'message': 'Test boshlash mumkin'}, status=status.HTTP_200_OK)












# core/views.py

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

        # Test vaqti tekshiruvi
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










# core/views.py

class FinishTestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, test_id):
        user = request.user
        try:
            test = Test.objects.get(id=test_id)
        except Test.DoesNotExist:
            return Response({'error': 'Test topilmadi'}, status=404)

        # Tekshiramiz, agar talaba allaqachon testni topshirgan bo‘lsa
        if StudentTest.objects.filter(student=user.student, test=test).exists():
            return Response({'error': 'Siz bu testni allaqachon topshirdingiz'}, status=403)

        # Test yakunlandi deb belgilaymiz
        StudentTest.objects.create(student=user.student, test=test)

        return Response({'message': 'Test muvaffaqiyatli yakunlandi'})


# --------------------------TEMPLATES---------------------------



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Test, Question, StudentTest, Answer
from datetime import datetime, timedelta
from django.utils import timezone

# Login sahifasi
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_student:
                return redirect('test_list')
            elif user.is_teacher:
                return redirect('teacher_dashboard')
        return render(request, 'login.html', {'error': 'Noto‘g‘ri login yoki parol'})
    return render(request, 'login.html')

# Test ro’yxati
@login_required
def test_list_view(request):
    if not request.user.is_student:
        return redirect('teacher_dashboard')
    tests = Test.objects.filter(start_time__lte=timezone.now(), end_time__gte=timezone.now())
    return render(request, 'test_list.html', {'tests': tests})

# Test detallari
@login_required
def test_detail_view(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    student_test = StudentTest.objects.filter(student__user=request.user, test=test).first()
    if not student_test or student_test.is_completed:
        return render(request, 'test_detail.html', {'test': test, 'error': 'Test boshlanmagan yoki tugallangan'})
    questions = Question.objects.filter(test=test)
    return render(request, 'test_detail.html', {'test': test, 'questions': questions, 'student_test': student_test})

# Testni boshlash
@login_required
def start_test_view(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    student = get_object_or_404(Student, user=request.user)
    if request.method == 'POST':
        student_test, created = StudentTest.objects.get_or_create(
            student=student,
            test=test,
            defaults={
                'start_time': timezone.now(),
                'duration': timedelta(minutes=60),  # 1 soatlik test
                'end_time': timezone.now() + timedelta(minutes=60)
            }
        )
        if not created and student_test.is_completed:
            return render(request, 'test_detail.html', {'test': test, 'error': 'Test allaqachon tugallangan'})
        return redirect('test_detail', test_id=test_id)
    return render(request, 'test_detail.html', {'test': test})

# Javob yuborish
@login_required
def submit_answer_view(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    student = get_object_or_404(Student, user=request.user)
    student_test = get_object_or_404(StudentTest, student=student, test=test)
    if student_test.end_time < timezone.now():
        return render(request, 'test_detail.html', {'test': test, 'error': 'Test vaqti tugagan'})
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        selected_option = request.POST.get('selected_option')
        question = get_object_or_404(Question, id=question_id, test=test)
        is_correct = selected_option.upper() == question.correct_option
        Answer.objects.create(
            student=student,
            question=question,
            selected_option=selected_option.upper(),
            is_correct=is_correct
        )
        if 'finish' in request.POST:
            student_test.is_completed = True
            student_test.save()
            return redirect('results', test_id=test_id)
        return redirect('test_detail', test_id=test_id)
    return render(request, 'submit_answer.html', {'test': test})

# Natijalar
@login_required
def results_view(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    student = get_object_or_404(Student, user=request.user)
    answers = Answer.objects.filter(student=student, question__test=test)
    total = answers.count()
    correct = answers.filter(is_correct=True).count()
    percentage = round(correct * 100 / total, 2) if total > 0 else 0
    return render(request, 'results.html', {'test': test, 'answers': answers, 'total': total, 'correct': correct, 'percentage': percentage})

# O‘qituvchi dashboard
@login_required
def teacher_dashboard_view(request):
    if not request.user.is_teacher:
        return redirect('test_list')
    tests = Test.objects.filter(created_by=request.user)
    return render(request, 'teacher/dashboard.html', {'tests': tests})

# Savol yuklash
@login_required
def upload_questions_view(request):
    if not request.user.is_teacher:
        return redirect('test_list')
    if request.method == 'POST':
        file = request.FILES.get('file')
        test_id = request.POST.get('test_id')
        if file and test_id:
            try:
                test = Test.objects.get(id=test_id, created_by=request.user)
                wb = openpyxl.load_workbook(file)
                sheet = wb.active
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    if len(row) < 6 or not all(row[:6]):
                        return render(request, 'teacher/upload_questions.html', {'error': 'Faylda yetishmayotgan ma‘lumotlar bor'})
                    Question.objects.create(
                        test=test,
                        text=row[0],
                        option_a=row[1],
                        option_b=row[2],
                        option_c=row[3],
                        option_d=row[4],
                        correct_option=row[5].upper()
                    )
                return render(request, 'teacher/upload_questions.html', {'success': 'Savollar muvaffaqiyatli yuklandi!'})
            except Test.DoesNotExist:
                return render(request, 'teacher/upload_questions.html', {'error': 'Test topilmadi'})
            except Exception as e:
                return render(request, 'teacher/upload_questions.html', {'error': f'Faylni o‘qishda xato: {str(e)}'})
        return render(request, 'teacher/upload_questions.html', {'error': 'Fayl va test_id kerak'})
    tests = Test.objects.filter(created_by=request.user)
    return render(request, 'teacher/upload_questions.html', {'tests': tests})

# Test statistikasi
@login_required
def test_statistics_view(request, test_id):
    if not request.user.is_teacher:
        return redirect('test_list')
    test = get_object_or_404(Test, id=test_id, created_by=request.user)
    answers = Answer.objects.filter(question__test=test).select_related('student', 'question')
    stats = {}
    for answer in answers:
        student_id = answer.student.student_id
        if student_id not in stats:
            stats[student_id] = {'correct': 0, 'total': 0}
        stats[student_id]['total'] += 1
        if answer.is_correct:
            stats[student_id]['correct'] += 1
    return render(request, 'teacher/statistics.html', {'test': test, 'stats': stats})
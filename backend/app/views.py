# core/views.py

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from .models import StudentTest, Test, Question, Answer, Student, User, Faculty, University
from .serializers import TestListSerializer, TestDetailSerializer, AnswerSubmitSerializer, ResultSerializer
import logging
import openpyxl

logger = logging.getLogger(__name__)

# DRF (REST API) viewlar endi api_views.py faylida. Bu faylda faqat template-based (render, redirect) viewlar qoldi.

# --------------------------TEMPLATES---------------------------

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Test, Question, StudentTest, Answer
from datetime import datetime, timedelta
from django.utils import timezone
from .forms import AddStudentForm
import random
from django.core.paginator import Paginator

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
    student = Student.objects.filter(user=request.user).first()
    if not student:
        return render(request, 'test_list.html', {'tests': []})
    tests = Test.objects.filter(
        start_time__lte=timezone.now(),
        end_time__gte=timezone.now(),
        group=student.group
    )
    return render(request, 'test_list.html', {'tests': tests})

# Test detallari
@login_required
def test_detail_view(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    student_test = StudentTest.objects.filter(student__user=request.user, test=test).first()
    if not student_test or (student_test.is_completed if student_test else False):
        return render(request, 'test_detail.html', {'test': test, 'error': 'Test boshlanmagan yoki tugallangan'})
    questions = Question.objects.filter(test=test)
    return render(request, 'test_detail.html', {'test': test, 'questions': questions, 'student_test': student_test})

# Testni boshlash
@login_required
def start_test_view(request, test_id):
    logger.info(f"start_test_view: test_id={test_id}, user={request.user}")
    test = get_object_or_404(Test, id=test_id)
    try:
        student = Student.objects.get(user=request.user)
        logger.info(f"Student found: {student}")
    except Student.DoesNotExist:
        logger.warning(f"Student not found for user {request.user}")
        return redirect('test_list')
    if request.method == 'POST':
        logger.info("POST so'rov: testni boshlash harakati")
        student_test, created = StudentTest.objects.get_or_create(
            student=student,
            test=test
        )
        logger.info(f"StudentTest: {student_test}, created={created}")
        if not created and (student_test.is_completed if student_test else False):
            logger.info("Test allaqachon tugallangan")
            return render(request, 'test_detail.html', {'test': test, 'error': 'Test allaqachon tugallangan'})
        questions = Question.objects.filter(test=test)
        return render(request, 'test_detail.html', {'test': test, 'questions': questions, 'student_test': student_test})
    else:
        logger.info("GET so'rov: testni boshlash sahifasi")
        student_test = StudentTest.objects.filter(student=student, test=test).first()
        if student_test and not student_test.is_completed:
            logger.info("Test allaqachon boshlangan, test_detail sahifasiga o'tkaziladi")
            questions = Question.objects.filter(test=test)
            return render(request, 'test_detail.html', {'test': test, 'questions': questions, 'student_test': student_test})
        logger.info("Test hali boshlanmagan, boshlash tugmasi ko'rsatiladi")
        return render(request, 'test_detail.html', {'test': test, 'show_start_button': True})

# Javob yuborish
@login_required
def submit_answer_view(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    student = get_object_or_404(Student, user=request.user)
    student_test = get_object_or_404(StudentTest, student=student, test=test)
    if test.end_time < timezone.now() or student_test.is_completed:
        return render(request, 'test_detail.html', {'test': test, 'error': 'Test vaqti tugagan yoki yakunlangan'})
    if request.method == 'POST':
        questions = Question.objects.filter(test=test)
        total = questions.count()
        correct = 0
        for question in questions:
            selected_option = request.POST.get(f'selected_option_{question.id}')
            if selected_option:
                is_correct = selected_option.upper() == question.correct_option
                Answer.objects.update_or_create(
                    student=student,
                    question=question,
                    defaults={
                        'selected_option': selected_option.upper(),
                        'is_correct': is_correct
                    }
                )
                if is_correct:
                    correct += 1
        if 'finish' in request.POST or test.end_time < timezone.now():
            student_test.is_completed = True
            student_test.completed_at = timezone.now()
            student_test.save()
            percentage = round(correct * 100 / total, 2) if total > 0 else 0
            answers = Answer.objects.filter(student=student, question__test=test)
            return redirect('results', test_id=test_id)
        return redirect('test_detail', test_id=test_id)
    questions = Question.objects.filter(test=test)
    return render(request, 'test_detail.html', {'test': test, 'questions': questions, 'student_test': student_test})

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
    paginator = Paginator(tests, 8)  # 8 ta test har bir sahifada
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'teacher/dashboard.html', {'tests': page_obj, 'page_obj': page_obj})

# Savol yuklash
@login_required
def upload_questions_view(request):
    if not request.user.is_teacher:
        return redirect('test_list')
    if request.method == 'POST':
        file = request.FILES.get('file')
        test_title = request.POST.get('test_title')
        test_subject = request.POST.get('test_subject')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        if file and test_title and test_subject and start_time and end_time:
            group = request.POST.get('group')
            import openpyxl
            from django.utils.dateparse import parse_datetime
            try:
                # Test yaratish
                test = Test.objects.create(
                    title=test_title,
                    subject=test_subject,
                    created_by=request.user,
                    start_time=parse_datetime(start_time),
                    end_time=parse_datetime(end_time),
                    group=group
                )
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
                return render(request, 'teacher/upload_questions.html', {'success': 'Test va savollar muvaffaqiyatli yaratildi!'})
            except Exception as e:
                return render(request, 'teacher/upload_questions.html', {'error': f'Faylni o‘qishda xato: {str(e)}'})
        return render(request, 'teacher/upload_questions.html', {'error': 'Barcha maydonlarni to‘ldiring va fayl tanlang!'})
    return render(request, 'teacher/upload_questions.html')

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
    # Foizni hisoblash
    for student_id, data in stats.items():
        data['percent'] = round((data['correct'] / data['total']) * 100, 2) if data['total'] > 0 else 0
    return render(request, 'teacher/statistics.html', {'test': test, 'stats': stats})

# Talabalar ro'yxati va qo'shish (faqat o'qituvchilar uchun)
@login_required
def student_list_view(request):
    if not request.user.is_teacher:
        return redirect('test_list')
    students = Student.objects.filter(faculty__in=Faculty.objects.filter(university__in=University.objects.all()), user__is_student=True)
    paginator = Paginator(students, 10)  # 10 ta student har bir sahifada
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'teacher/student_list.html', {'students': page_obj, 'page_obj': page_obj})

@login_required
def add_student_view(request):
    if not request.user.is_teacher:
        return redirect('test_list')
    if request.method == 'POST':
        form = AddStudentForm(request.POST)
        if form.is_valid():
            # Student ID generatsiya
            student_id = str(random.randint(100000, 999999))
            # User yaratish (parol student_id, username ismi bilan bir xil)
            user = User.objects.create_user(
                username=form.cleaned_data['first_name'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                is_student=True,
                password=student_id
            )
            # Student yaratish
            Student.objects.create(
                user=user,
                student_id=student_id,
                faculty=form.cleaned_data['faculty'],
                course=form.cleaned_data.get('course', ''),
                group=form.cleaned_data.get('group', '')
            )
            return redirect('student_list')
    else:
        form = AddStudentForm()
    return render(request, 'teacher/add_student.html', {'form': form})

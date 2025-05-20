from django.urls import path
from .views import (
    FinishTestView, RegisterStudentView, StartTestView, SubmitAnswerView,
    TestListView, TestDetailView, SubmitAnswersView, TestStatisticsView,
    UploadQuestionsFromExcelView, login_view, test_list_view, test_detail_view,
    start_test_view, submit_answer_view, results_view, teacher_dashboard_view,
    upload_questions_view, test_statistics_view
)

urlpatterns = [
    # API endpointlari
    path('tests/', TestListView.as_view(), name='test_list_api'),
    path('tests/<int:test_id>/', TestDetailView.as_view(), name='test_detail_api'),
    path('submit-answers/', SubmitAnswersView.as_view(), name='submit_answers_api'),
    path('upload-questions/', UploadQuestionsFromExcelView.as_view(), name='upload_questions_api'),
    path('register-student/', RegisterStudentView.as_view(), name='register_student_api'),
    path('test-statistics/<int:test_id>/', TestStatisticsView.as_view(), name='test_statistics_api'),
    path('start-test/<int:test_id>/', StartTestView.as_view(), name='start_test_api'),
    path('answer/<int:test_id>/', SubmitAnswerView.as_view(), name='submit_answer_api'),
    path('finish-test/<int:test_id>/', FinishTestView.as_view(), name='finish_test_api'),
    # Shablonlar uchun view’lar
    path('', login_view, name='login'),
    path('tests-list/', test_list_view, name='test_list'),  # tests/ nizo oldini olish uchun
    path('test/<int:test_id>/', test_detail_view, name='test_detail'),
    path('begin-test/<int:test_id>/', start_test_view, name='start_test'),
    path('submit/<int:test_id>/', submit_answer_view, name='submit_answer'),
    path('results/<int:test_id>/', results_view, name='results'),
    path('teacher/dashboard/', teacher_dashboard_view, name='teacher_dashboard'),
    path('teacher/upload-questions/', upload_questions_view, name='upload_questions'),
    path('teacher/statistics/<int:test_id>/', test_statistics_view, name='test_statistics'),
]
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.views import generic
from .models import Course, Enrollment, Question, Choice, Submission
import logging

logger = logging.getLogger(__name__)

def registration_request(request):
    context = {}
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('psw', '')
        first_name = request.POST.get('first_name', '') 
        last_name = request.POST.get('last_name', '')  
        
        # Validate that all fields are filled
        if not all([username, password, first_name, last_name]):
            context['message'] = "All fields are required."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)

        # Check if the user already exists
        if User.objects.filter(username=username).exists():
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
        else:
            # Create and log in the new user
            user = User.objects.create_user(
                username=username, 
                first_name=first_name, 
                last_name=last_name, 
                password=password
            )
            login(request, user)
            logger.info(f"New user registered: {username}")
            return redirect("onlinecourse:index")
    
    return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            logger.info(f"User logged in: {username}")
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    return render(request, 'onlinecourse/user_login_bootstrap.html', context)

def logout_request(request):
    logger.info(f"User logged out: {request.user.username}")
    logout(request)
    return redirect('onlinecourse:index')

def check_if_enrolled(user, course):
    return Enrollment.objects.filter(user=user, course=course).exists()

class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        if user.is_authenticated:
            for course in courses:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses

class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'

def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    if user.is_authenticated and not check_if_enrolled(user, course):
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()
        logger.info(f"User enrolled in course: {course.name} (ID: {course_id})")

    return HttpResponseRedirect(reverse('onlinecourse:course_details', args=(course.id,)))

def exam_page(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    questions = Question.objects.filter(course=course)
    
    print(f"Course: {course.name}")
    print(f"Number of Questions: {questions.count()}")

    context = {
        'course': course,
        'questions': questions,
    }
    return render(request, 'onlinecourse/exam_page.html', context)

def submit_exam(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    enrollment = get_object_or_404(Enrollment, user=user, course=course)
    submission = Submission.objects.create(enrollment=enrollment)
    choices = extract_answer(request)
    submission.choices.set(choices)
    logger.info(f"Submission made by user {user.username} for course {course.name} (ID: {course_id})")
    return HttpResponseRedirect(reverse('onlinecourse:exam_result', args=(course_id, submission.id)))

def extract_answer(request):
    return [int(value) for key, value in request.POST.items() if key.startswith('choice')]

def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    choices = submission.choices.all()

    total_score = sum(choice.question.grade for choice in choices if choice.is_correct)

    context = {
        'course': course,
        'grade': total_score,
        'choices': choices,
    }

    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)

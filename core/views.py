from django.http import HttpRequest, HttpResponse
from django.conf import settings
from rest_framework.views import APIView
from django.db import connection
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .models import User
from .serializers import UserRegistrationSerializer
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from .models import Question, Assignment, AssignmentItem
from .serializers import AssignmentSerializer
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import random
from django.http import JsonResponse
from .serializers import StudentDropdownSerializer
from rest_framework import generics
from .serializers import StudentListSerializer


def home(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Welcome to TME Django project!")


class AuthRegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User created successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AuthLoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken
        # Accept a single `identifier` field (preferred) which can be email or username.
        # Keep backward compatibility with `email` or `username` fields.
        email_or_username = (
            request.data.get('identifier') or
            request.data.get('email') or
            request.data.get('username')
        )
        password = request.data.get('password')
        if not email_or_username or not password:
            return Response({
                "error": "Email/username and password are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        # Try to find user by email or username
        user = None
        if '@' in email_or_username:
            try:
                user = User.objects.get(email=email_or_username)
            except User.DoesNotExist:
                pass
        else:
            try:
                user = User.objects.get(username=email_or_username)
            except User.DoesNotExist:
                pass
        # Check password
        if user and check_password(password, user.password):
            # Update last login
            user.last_login = timezone.now()
            user.save()
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Login successful",
                "access_token": str(refresh.access_token),
                "access_token_type": "access",
                "refresh_token": str(refresh),
                "refresh_token_type": "refresh",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "error": "Invalid email/username or password"
            }, status=status.HTTP_401_UNAUTHORIZED)


class AssignmentCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
                from .serializers import QuestionSerializer
                assignments = Assignment.objects.all()
                data = []
                for assignment in assignments:
                    items = AssignmentItem.objects.filter(assignment=assignment)
                    questions = []
                    for item in items:
                        q_data = QuestionSerializer(item.question).data
                        # Add assignment title to each question object
                        q_data['title'] = assignment.title
                        questions.append(q_data)
                    data.append({
                        'id': assignment.id,
                        'teacher': assignment.teacher.username if assignment.teacher else None,
                        'title': assignment.title,
                        'concept': assignment.concept,
                        'length_of_question': assignment.length_of_question,
                        'number_of_questions': assignment.number_of_questions,
                        'speed': assignment.speed,
                        'assign_type': assignment.assign_type,
                        'target_student': assignment.target_student.username if assignment.target_student else None,
                        'target_class_section': assignment.target_class_section,
                        'created_at': assignment.created_at,
                        'questions': questions
                    })
                return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": "Internal server error", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Utility for testing: update student1's email to altafhassan994@gmail.com
    # with connection.cursor() as cursor:
    #     cursor.execute("UPDATE core_user SET email = %s WHERE id = %s", ["altafhassan994@gmail.com", 1])

    def post(self, request):
        try:
            # Expected payload: concept, length_of_question, number_of_questions, speed, assign_type ('individual'|'class'), target_student (id) or target_class_section
            data = request.data
            title = data.get('title')
            concept = data.get('concept')
            length_of_question = data.get('length_of_question')
            number_of_questions = int(data.get('number_of_questions', 0))
            speed = int(data.get('speed', 30))
            assign_type = data.get('assign_type')

            if not concept or not length_of_question or not number_of_questions:
                return Response({"error": "Missing required fields: concept, length_of_question, number_of_questions are required."}, status=status.HTTP_400_BAD_REQUEST)

            # assign_type can be any string (e.g., class section name)
            # target_student can be a username or numeric ID
            target_student_val = data.get('target_student')
            target_student_obj = None
            if target_student_val:
                # Try to get by ID first, then by username
                try:
                    target_student_obj = User.objects.get(id=int(target_student_val))
                except (TypeError, ValueError, User.DoesNotExist):
                    try:
                        target_student_obj = User.objects.get(username=target_student_val)
                    except User.DoesNotExist:
                        return Response({"error": f"No user found with id or username '{target_student_val}'."}, status=status.HTTP_400_BAD_REQUEST)

            # Find candidate questions (using 'complexity' instead of 'concept')
            candidates = Question.objects.filter(complexity__iexact=concept, length=length_of_question)
            if candidates.count() < number_of_questions:
                return Response({"error": "Not enough questions available for the given filters"}, status=status.HTTP_400_BAD_REQUEST)

            # Create assignment
            teacher = request.user if isinstance(request.user, User) else get_object_or_404(User, username=request.user.username)
            assignment = Assignment.objects.create(
                teacher=teacher,
                title=title or '',
                concept=concept,
                length_of_question=length_of_question,
                number_of_questions=number_of_questions,
                speed=speed,
                assign_type=assign_type,
                target_student=target_student_obj,
                target_class_section=data.get('target_class_section') if data.get('target_class_section') else None,
            )

            # Send email notification to student if assigned
            if assignment.target_student and assignment.target_student.email:
                from django.core.mail import send_mail
                send_mail(
                    'New Assignment Notification',
                    f'Hello {assignment.target_student.first_name},\n\nYou have been assigned a new assignment: {assignment.title}.',
                    'altafhassan994@gmail.com',  # Sender email
                    ['altafhassan994@gmail.com'],  # Force recipient for testing
                    fail_silently=False,
                )
                print(f"Email sent to altafhassan994@gmail.com for assignment '{assignment.title}'")

            # Pick random questions
            question_ids = list(candidates.values_list('id', flat=True))
            chosen = random.sample(question_ids, number_of_questions)
            items = []
            for idx, qid in enumerate(chosen):
                q = Question.objects.get(id=qid)
                ai = AssignmentItem.objects.create(assignment=assignment, question=q, order_index=idx)
                items.append(ai)

            serializer = AssignmentSerializer(assignment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": "Internal server error", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentsSectionsView(APIView):
    permission_classes = []  # allow any for dropdown usage; change if needed

    def get(self, request):
        # list all students and distinct class sections
        students = User.objects.filter(role='student')
        student_ser = StudentDropdownSerializer(students, many=True)
        sections = User.objects.exclude(class_section__isnull=True).exclude(class_section__exact='').values_list('class_section', flat=True).distinct()
        return JsonResponse({'students': student_ser.data, 'sections': list(sections)})


class StudentsAndSectionsView(APIView):
    permission_classes = []

    def get(self, request):
        # list all students and distinct class sections
        students = User.objects.filter(role='student')
        student_ser = StudentDropdownSerializer(students, many=True)
        sections = User.objects.exclude(class_section__isnull=True).exclude(class_section__exact='').values_list('class_section', flat=True).distinct()
        return Response({'students': student_ser.data, 'sections': list(sections)}, status=status.HTTP_200_OK)


class StudentListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentListSerializer

    def get_queryset(self):
        return User.objects.filter(role='student')


class SectionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sections = User.objects.exclude(class_section__isnull=True).exclude(class_section__exact='').values_list('class_section', flat=True).distinct()
        return Response(list(sections))

# Question endpoints removed from views.

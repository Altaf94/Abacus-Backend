from django.urls import path
from .views import AuthRegisterView, AuthLoginView, AssignmentCreateView, StudentsAndSectionsView

urlpatterns = [
    # Authentication
    path('auth/register/', AuthRegisterView.as_view(), name='auth_register'),
    path('auth/login/', AuthLoginView.as_view(), name='auth_login'),

    # Assignments
    path('assignments/', AssignmentCreateView.as_view(), name='assignments_create'),

    # Combined students + sections for dropdowns
    path('students_sections/', StudentsAndSectionsView.as_view(), name='students_and_sections'),
]

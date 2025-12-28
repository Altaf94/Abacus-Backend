from rest_framework import serializers
from .models import User, Question, Assignment, AssignmentItem
from django.contrib.auth.hashers import make_password


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'confirm_password', 'first_name', 'last_name', 'role',
            'class_section', 'roll_number', 'teacher_id'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'role': {'required': True}
        }
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        # Role-specific validation
        role = data.get('role')
        if role == 'student':
            if not data.get('class_section') or not data.get('roll_number'):
                raise serializers.ValidationError({
                    'class_section': 'class_section and roll_number are required for students',
                })
        elif role == 'teacher':
            if not data.get('teacher_id'):
                raise serializers.ValidationError({
                    'teacher_id': 'teacher_id is required for teachers',
                })
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        validated_data['password'] = make_password(validated_data['password'])
        user = User.objects.create(**validated_data)
        return user


class AssignmentItemSerializer(serializers.ModelSerializer):
    question_serial = serializers.IntegerField(source='question.serial', read_only=True)

    class Meta:
        model = AssignmentItem
        fields = ['question_serial', 'order_index', 'is_answered']


class AssignmentSerializer(serializers.ModelSerializer):
    items = AssignmentItemSerializer(many=True, read_only=True)

    class Meta:
        model = Assignment
        fields = ['id', 'teacher', 'title', 'concept', 'length_of_question', 'number_of_questions', 'speed', 'assign_type', 'target_student', 'target_class_section', 'created_at', 'items']


class StudentDropdownSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'class_section', 'roll_number']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class StudentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'class_section', 'roll_number']

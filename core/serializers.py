from rest_framework import serializers
from .models import AbacusExercise, Question, LiveSession, AssignedQuestion

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            'id', 'concept', 'content', 'length_of_question', 'created_at'
        ]


class AbacusExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbacusExercise
        fields = ['id', 'concept', 'length_of_question', 'number_of_questions', 'speed', 'created_at']


class AssignedQuestionSerializer(serializers.ModelSerializer):
	class Meta:
		model = AssignedQuestion
		fields = ['id', 'order_index', 'assigned_at', 'is_answered', 'legacy_serial', 'content', 'session_code']


class LiveSessionCreateSerializer(serializers.Serializer):
	teacher_identifier = serializers.CharField(max_length=100)
	concept = serializers.CharField(max_length=100)
	length_of_question = serializers.IntegerField(min_value=1)
	number_of_questions = serializers.IntegerField(min_value=1)
	speed = serializers.IntegerField(min_value=1)


class LiveSessionSerializer(serializers.ModelSerializer):
	assigned_questions = serializers.SerializerMethodField()
	class Meta:
		model = LiveSession
		fields = [
			'id', 'session_code', 'teacher_identifier', 'student_identifier', 'concept',
			'length_of_question', 'speed', 'created_at', 'is_active', 'current_index',
			'assigned_questions'
		]

	def get_assigned_questions(self, obj):
		qs = AssignedQuestion.objects.filter(session_code=obj.session_code).order_by('order_index')
		return AssignedQuestionSerializer(qs, many=True).data

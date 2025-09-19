from django.contrib import admin
from .models import AbacusExercise, Question


@admin.register(AbacusExercise)
class AbacusExerciseAdmin(admin.ModelAdmin):
	list_display = ("id", "concept", "length_of_question", "number_of_questions", "speed", "created_at")
	search_fields = ("concept",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
	list_display = ("id", "concept", "length_of_question", "created_at")
	search_fields = ("concept", "content")

# Register your models here.

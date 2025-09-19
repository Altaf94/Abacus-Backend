from django.db import models


# Bank of available questions to pick from
class Question(models.Model):
	concept = models.CharField(max_length=100)
	content = models.TextField()
	length_of_question = models.PositiveIntegerField(help_text="Length of question (e.g., digits or terms)")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = 'core_question_orm'


	def __str__(self) -> str:
		return f"[{self.concept}] len={self.length_of_question} - {self.content[:30]}..."


# Model to store abacus exercise parameters and selected questions
class AbacusExercise(models.Model):
	concept = models.CharField(max_length=100)
	length_of_question = models.PositiveIntegerField()
	number_of_questions = models.PositiveIntegerField()
	speed = models.PositiveIntegerField(help_text="Speed in seconds or as per requirement")
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.concept} - {self.number_of_questions} questions"


# Live teacher-student session for synchronized questions
class LiveSession(models.Model):
	session_code = models.CharField(max_length=32, unique=True)
	teacher_identifier = models.CharField(max_length=100)
	student_identifier = models.CharField(max_length=100, blank=True)
	concept = models.CharField(max_length=100)
	length_of_question = models.PositiveIntegerField()
	speed = models.PositiveIntegerField(help_text="Speed in seconds or as per requirement")
	created_at = models.DateTimeField(auto_now_add=True)
	is_active = models.BooleanField(default=True)
	current_index = models.PositiveIntegerField(default=0, help_text="0-based pointer to current question in session")

	def __str__(self) -> str:
		return f"Session {self.session_code} ({self.concept})"



class AssignedQuestion(models.Model):
	session_code = models.CharField(max_length=32)
	legacy_serial = models.CharField(max_length=255, blank=True)
	content = models.TextField(blank=True)
	order_index = models.PositiveIntegerField(help_text="0-based order in session")
	assigned_at = models.DateTimeField(auto_now_add=True)
	is_answered = models.BooleanField(default=False)

	class Meta:
		unique_together = ("session_code", "order_index")
		ordering = ["order_index", "id"]

	def __str__(self) -> str:
		return f"{self.session_code} #{self.order_index}"


# Unmanaged mapping to the existing legacy table core_question (uppercase columns)
class LegacyQuestion(models.Model):
	serial = models.CharField(max_length=255, db_column='Serial', primary_key=True)
	a = models.CharField(max_length=255, db_column='A', blank=True)
	b = models.CharField(max_length=255, db_column='B', blank=True)
	c = models.CharField(max_length=255, db_column='C', blank=True)
	d = models.CharField(max_length=255, db_column='D', blank=True)
	e = models.CharField(max_length=255, db_column='E', blank=True)
	f = models.CharField(max_length=255, db_column='F', blank=True)
	g = models.CharField(max_length=255, db_column='G', blank=True)
	h = models.CharField(max_length=255, db_column='H', blank=True)
	i = models.CharField(max_length=255, db_column='I', blank=True)
	j = models.CharField(max_length=255, db_column='J', blank=True)
	k = models.CharField(max_length=255, db_column='K', blank=True)
	l = models.CharField(max_length=255, db_column='L', blank=True)
	m = models.CharField(max_length=255, db_column='M', blank=True)
	n = models.CharField(max_length=255, db_column='N', blank=True)
	o = models.CharField(max_length=255, db_column='O', blank=True)
	p = models.CharField(max_length=255, db_column='P', blank=True)
	q = models.CharField(max_length=255, db_column='Q', blank=True)
	r = models.CharField(max_length=255, db_column='R', blank=True)
	s = models.CharField(max_length=255, db_column='S', blank=True)
	t = models.CharField(max_length=255, db_column='T', blank=True)
	answer = models.CharField(max_length=255, db_column='ANSWER', blank=True)
	complexity = models.CharField(max_length=255, db_column='Complexity')
	length = models.CharField(max_length=255, db_column='Length')

	class Meta:
		managed = False
		db_table = 'core_question_orm'

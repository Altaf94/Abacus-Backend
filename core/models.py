from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class UserManager(BaseUserManager):
	def create_user(self, username, email, password=None, **extra_fields):
		if not email:
			raise ValueError('Email is required')
		email = self.normalize_email(email)
		user = self.model(username=username, email=email, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, username, email, password=None, **extra_fields):
		extra_fields.setdefault('is_staff', True)
		extra_fields.setdefault('is_superuser', True)
		return self.create_user(username, email, password, **extra_fields)

# Custom User model for registration/login with student/teacher role
class User(AbstractBaseUser, PermissionsMixin):
	username = models.CharField(max_length=150, unique=True)
	email = models.EmailField(unique=True)
	password = models.CharField(max_length=128)
	first_name = models.CharField(max_length=150, blank=True)
	last_name = models.CharField(max_length=150, blank=True)
	role = models.CharField(max_length=10, choices=[('student', 'Student'), ('teacher', 'Teacher')])
	is_active = models.BooleanField(default=True)
	is_staff = models.BooleanField(default=False)
	# For students
	class_section = models.CharField(max_length=20, blank=True, null=True)
	roll_number = models.CharField(max_length=20, blank=True, null=True)
	# For teachers
	teacher_id = models.CharField(max_length=150, blank=True, null=True)
	date_joined = models.DateTimeField(auto_now_add=True)
	last_login = models.DateTimeField(null=True, blank=True)


	objects = UserManager()

	REQUIRED_FIELDS = ['email']
	USERNAME_FIELD = 'username'

	class Meta:
		db_table = 'core_user'

	def __str__(self):
		return f"{self.username} ({self.role})"


# Centralized Question Bank
class Question(models.Model):
	serial = models.IntegerField(unique=True, help_text="Serial number of the question")
	a = models.CharField(max_length=50, blank=True, null=True, help_text="Column A")
	b = models.CharField(max_length=50, blank=True, null=True, help_text="Column B")
	c = models.CharField(max_length=50, blank=True, null=True, help_text="Column C")
	d = models.CharField(max_length=50, blank=True, null=True, help_text="Column D")
	e = models.CharField(max_length=50, blank=True, null=True, help_text="Column E")
	f = models.CharField(max_length=50, blank=True, null=True, help_text="Column F")
	g = models.CharField(max_length=50, blank=True, null=True, help_text="Column G")
	h = models.CharField(max_length=50, blank=True, null=True, help_text="Column H")
	i = models.CharField(max_length=50, blank=True, null=True, help_text="Column I")
	j = models.CharField(max_length=50, blank=True, null=True, help_text="Column J")
	k = models.CharField(max_length=50, blank=True, null=True, help_text="Column K")
	l = models.CharField(max_length=50, blank=True, null=True, help_text="Column L")
	m = models.CharField(max_length=50, blank=True, null=True, help_text="Column M")
	n = models.CharField(max_length=50, blank=True, null=True, help_text="Column N")
	o = models.CharField(max_length=50, blank=True, null=True, help_text="Column O")
	p = models.CharField(max_length=50, blank=True, null=True, help_text="Column P")
	q = models.CharField(max_length=50, blank=True, null=True, help_text="Column Q")
	r = models.CharField(max_length=50, blank=True, null=True, help_text="Column R")
	s = models.CharField(max_length=50, blank=True, null=True, help_text="Column S")
	t = models.CharField(max_length=50, blank=True, null=True, help_text="Column T")
	answer = models.CharField(max_length=100, help_text="Correct answer")
	complexity = models.CharField(max_length=50, blank=True, null=True, help_text="Question complexity/difficulty")
	length = models.IntegerField(blank=True, null=True, help_text="Length of question")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'core_question'

	def __str__(self):
		return f"Question #{self.serial} - Answer: {self.answer}"


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


class Assignment(models.Model):
	ASSIGN_TYPE_CHOICES = [
		('individual', 'Individual'),
		('class', 'Class'),
	]

	teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments')
	title = models.CharField(max_length=255, blank=True)
	concept = models.CharField(max_length=100)
	length_of_question = models.PositiveIntegerField()
	number_of_questions = models.PositiveIntegerField()
	speed = models.PositiveIntegerField(help_text='Speed in seconds')
	assign_type = models.CharField(max_length=20, choices=ASSIGN_TYPE_CHOICES)
	target_student = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='assigned_to')
	target_class_section = models.CharField(max_length=50, blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Assignment by {self.teacher.username} ({self.assign_type}) - {self.concept} x{self.number_of_questions}"


class AssignmentItem(models.Model):
	assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='items')
	question = models.ForeignKey(Question, on_delete=models.CASCADE)
	order_index = models.PositiveIntegerField()
	assigned_at = models.DateTimeField(auto_now_add=True)
	is_answered = models.BooleanField(default=False)

	class Meta:
		unique_together = ('assignment', 'order_index')

	def __str__(self):
		return f"{self.assignment.id} - Q#{self.order_index} -> {self.question.serial}"


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

from django.http import HttpRequest, HttpResponse


def home(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Welcome to TME Django project!")


# API view to handle POST for AbacusExercise
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .models import AbacusExercise, Question, LiveSession, AssignedQuestion, LegacyQuestion
from .serializers import (
    AbacusExerciseSerializer,
    QuestionSerializer,
    LiveSessionCreateSerializer,
    LiveSessionSerializer,
    AssignedQuestionSerializer,
)
from django.utils.crypto import get_random_string
from django.db import connection
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

class AbacusExerciseCreateView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = AbacusExerciseSerializer(data=request.data)
        if serializer.is_valid():
            # Create exercise first
            exercise: AbacusExercise = AbacusExercise.objects.create(
                concept=serializer.validated_data['concept'],
                length_of_question=serializer.validated_data['length_of_question'],
                number_of_questions=serializer.validated_data['number_of_questions'],
                speed=serializer.validated_data['speed'],
            )
            exercise.save()
            out = AbacusExerciseSerializer(exercise)
            return Response(out.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AbacusExerciseQuestionsView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, pk: int):
        try:
            exercise = AbacusExercise.objects.get(pk=pk)
        except AbacusExercise.DoesNotExist:
            return Response({"detail": "Exercise not found"}, status=status.HTTP_404_NOT_FOUND)
        # Relationships removed; return empty list for compatibility
        return Response([])


class LiveSessionCreateView(APIView):
	permission_classes = [AllowAny]
	def post(self, request):
		serializer = LiveSessionCreateSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		concept = serializer.validated_data['concept']
		length_of_question = serializer.validated_data['length_of_question']
		number_of_questions = serializer.validated_data['number_of_questions']
		speed = serializer.validated_data['speed']
		teacher_identifier = serializer.validated_data['teacher_identifier']

		# select questions from bank
		qs = Question.objects.filter(
			concept=concept,
			length_of_question=length_of_question,
		).order_by('id')[: number_of_questions]
		if qs.count() < number_of_questions:
			remaining = number_of_questions - qs.count()
			extra = Question.objects.filter(concept=concept).exclude(id__in=qs.values('id')).order_by('id')[: remaining]
			selected = list(qs) + list(extra)
		else:
			selected = list(qs)

		session_code = get_random_string(8)
		session = LiveSession.objects.create(
			session_code=session_code,
			teacher_identifier=teacher_identifier,
			concept=concept,
			length_of_question=length_of_question,
			speed=speed,
		)

		assigned = []
		for idx, q in enumerate(selected):
			assigned.append(AssignedQuestion(session_code=session.session_code, order_index=idx, content=q.content))
		AssignedQuestion.objects.bulk_create(assigned)

		return Response(LiveSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class LiveSessionJoinView(APIView):
	permission_classes = [AllowAny]
	def post(self, request, session_code: str):
		student_identifier = request.data.get('student_identifier')
		if not student_identifier:
			return Response({"student_identifier": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
		try:
			session = LiveSession.objects.get(session_code=session_code, is_active=True)
		except LiveSession.DoesNotExist:
			return Response({"detail": "Session not found"}, status=status.HTTP_404_NOT_FOUND)
		session.student_identifier = student_identifier
		session.save(update_fields=["student_identifier"])
		return Response(LiveSessionSerializer(session).data)


class LiveSessionCurrentQuestionView(APIView):
	permission_classes = [AllowAny]
	def get(self, request, session_code: str):
		try:
			session = LiveSession.objects.get(session_code=session_code, is_active=True)
		except LiveSession.DoesNotExist:
			return Response({"detail": "Session not found"}, status=status.HTTP_404_NOT_FOUND)
		current = AssignedQuestion.objects.filter(session_code=session.session_code, order_index=session.current_index).first()
		if not current:
			return Response({"detail": "No questions assigned"}, status=status.HTTP_404_NOT_FOUND)
		return Response(AssignedQuestionSerializer(current).data)


class LiveSessionAdvanceView(APIView):
	permission_classes = [AllowAny]
	def post(self, request, session_code: str):
		try:
			session = LiveSession.objects.get(session_code=session_code, is_active=True)
		except LiveSession.DoesNotExist:
			return Response({"detail": "Session not found"}, status=status.HTTP_404_NOT_FOUND)
		total = AssignedQuestion.objects.filter(session_code=session.session_code).count()
		if total == 0:
			return Response({"detail": "No questions to advance"}, status=status.HTTP_400_BAD_REQUEST)
		if session.current_index + 1 >= total:
			return Response({"detail": "End of session"}, status=status.HTTP_200_OK)
		session.current_index += 1
		session.save(update_fields=["current_index"])
		current = AssignedQuestion.objects.filter(session_code=session.session_code, order_index=session.current_index).first()
		return Response(AssignedQuestionSerializer(current).data)


class LiveSessionEndView(APIView):
	permission_classes = [AllowAny]
	def post(self, request, session_code: str):
		updated = LiveSession.objects.filter(session_code=session_code, is_active=True).update(is_active=False)
		if updated == 0:
			return Response({"detail": "Session not found"}, status=status.HTTP_404_NOT_FOUND)
		return Response({"detail": "Session ended"})


class LegacyQuestionsListView(APIView):
	permission_classes = [AllowAny]
	def post(self, request):
		concept = request.data.get('concept')
		length_of_question = request.data.get('length_of_question')
		number_of_questions = request.data.get('number_of_questions')
		student_id = request.data.get('student_id')
		teacher_id = request.data.get('teacher_id')
		section_id = request.data.get('section_id')
		speed = request.data.get('speed')
		activity_name = request.data.get('activity_name')
		
		# Handle null values for optional parameters
		if student_id is None or student_id == "":
			student_id = None
		if teacher_id is None or teacher_id == "":
			teacher_id = None
		if section_id is None or section_id == "":
			section_id = None
		if speed is None or speed == "":
			speed = None
		
		errors = {}
		if not concept:
			errors['concept'] = ["This field is required."]
		if length_of_question in (None, ""):
			errors['length_of_question'] = ["This field is required."]
		if not activity_name:
			errors['activity_name'] = ["This field is required."]
			
		# number_of_questions is optional; if provided, must be positive int
		limit_val = None
		if number_of_questions not in (None, ""):
			try:
				limit_val = int(number_of_questions)
			except (TypeError, ValueError):
				errors['number_of_questions'] = ["Must be an integer."]
			else:
				if limit_val <= 0:
					errors['number_of_questions'] = ["Must be greater than 0."]
					
		# speed is optional; if provided, must be a positive number (can be decimal)
		speed_val = None
		if speed is not None and speed != "":
			try:
				speed_val = float(speed)
			except (TypeError, ValueError):
				errors['speed'] = ["Must be a number."]
			else:
				if speed_val <= 0:
					errors['speed'] = ["Must be greater than 0."]
					
		if errors:
			return Response(errors, status=status.HTTP_400_BAD_REQUEST)
			
		# ensure str for legacy Length compare
		length_str = str(length_of_question)
		# Raw SQL to query from core_question table
		base_select = (
			"SELECT \"Serial\", \"A\", \"B\", \"C\", \"D\", \"E\", \"F\", \"G\", \"H\", \"I\", \"J\", "
			"\"K\", \"L\", \"M\", \"N\", \"O\", \"P\", \"Q\", \"R\", \"S\", \"T\", \"ANSWER\", \"Complexity\", \"Length\" "
			"FROM core_question WHERE \"Complexity\" = %s AND \"Length\" = %s ORDER BY \"Serial\""
		)
		# First, get the questions from core_question table
		with connection.cursor() as cursor:
			params = [concept, length_str]
			if limit_val is not None:
				query = base_select + " LIMIT %s"
				params.append(limit_val)
			else:
				query = base_select
			cursor.execute(query, params)
			rows = cursor.fetchall()
			cols = [
				"serial","A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","ANSWER","Complexity","Length"
			]
			data = [dict(zip(cols, row)) for row in rows]
			
		# Check if any questions were found
		if not data:
			return Response({
				"error": "No questions found",
				"message": f"No questions found with concept '{concept}' and length '{length_of_question}'",
				"concept": concept,
				"length_of_question": length_of_question,
				"suggestion": "Please check available concepts and lengths using GET /api/complexities/"
			}, status=status.HTTP_404_NOT_FOUND)
		
		# Insert selected questions into core_assignedquestion table
		insert_sql = (
			"INSERT INTO core_assignedquestion ("
			"serial, a, b, c, d, e, f, g, h, i, j, "
			"k, l, m, n, o, p, q, r, s, t, "
			"answer, complexity, length, student_id, teacher_id, activity_name, speed, section_id"
			") VALUES ("
			"%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
			"%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
			"%s, %s, %s, %s, %s, %s, %s, %s"
			")"
		)
		
		# Use a new cursor for the insert operation
		with connection.cursor() as insert_cursor:
			# Insert each selected question with the new parameters
			for row in data:
				# Extract values from the question data
				question_values = (
					row['serial'], row['A'], row['B'], row['C'], row['D'], row['E'], 
					row['F'], row['G'], row['H'], row['I'], row['J'],
					row['K'], row['L'], row['M'], row['N'], row['O'], row['P'], 
					row['Q'], row['R'], row['S'], row['T'],
					row['ANSWER'], row['Complexity'], row['Length'],
					student_id or None, teacher_id or None, activity_name, speed_val, section_id or None
				)
				insert_cursor.execute(insert_sql, question_values)
		
		# Add the additional parameters to the response
		response_data = {
			"questions": data,
			"student_id": student_id,
			"teacher_id": teacher_id,
			"section_id": section_id,
			"speed": speed_val,
			"activity_name": activity_name,
			"concept": concept,
			"length_of_question": length_of_question,
			"number_of_questions": limit_val,
			"total_count": len(data),
			"message": f"Successfully assigned {len(data)} questions"
		}
		
		return Response(response_data)


class AssignQuestionsSimpleView(APIView):
	permission_classes = [AllowAny]
	
	def get(self, request):
		# Get query parameters for filtering
		concept = request.query_params.get('concept')
		length = request.query_params.get('length')
		student_id = request.query_params.get('student_id')
		teacher_id = request.query_params.get('teacher_id')
		activity_name = request.query_params.get('activity_name')
		
		# Build WHERE clause based on provided parameters
		where_conditions = []
		where_params = []
		
		if concept:
			where_conditions.append("complexity = %s")
			where_params.append(concept)
		if length:
			where_conditions.append("length = %s")
			where_params.append(length)
		if student_id:
			where_conditions.append("student_id = %s")
			where_params.append(student_id)
		if teacher_id:
			where_conditions.append("teacher_id = %s")
			where_params.append(teacher_id)
		if activity_name:
			where_conditions.append("activity_name = %s")
			where_params.append(activity_name)
		
		# Build the query
		if where_conditions:
			where_clause = " AND ".join(where_conditions)
			query = f"SELECT serial, a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, answer, complexity, length, student_id, teacher_id, activity_name FROM core_assignedquestion WHERE {where_clause} ORDER BY serial"
		else:
			query = "SELECT serial, a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, answer, complexity, length, student_id, teacher_id, activity_name FROM core_assignedquestion ORDER BY serial"
		
		with connection.cursor() as cursor:
			cursor.execute(query, where_params)
			rows = cursor.fetchall()
			
			cols = [
				"serial", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j",
				"k", "l", "m", "n", "o", "p", "q", "r", "s", "t",
				"answer", "complexity", "length", "student_id", "teacher_id", "activity_name"
			]
			assigned_data = [dict(zip(cols, row)) for row in rows]
		
		return Response({
			"assigned_questions": assigned_data,
			"total_count": len(assigned_data)
		})
	
	def post(self, request):
		concept = request.data.get('concept')
		length_of_question = request.data.get('length_of_question')
		number_of_questions = request.data.get('number_of_questions')
		student_id = request.data.get('student_id')
		teacher_id = request.data.get('teacher_id')
		activity_name = request.data.get('activity_name')

		errors = {}
		if not concept:
			errors['concept'] = ["This field is required."]
		if length_of_question in (None, ""):
			errors['length_of_question'] = ["This field is required."]
		# student_id, teacher_id, and activity_name are optional
		# number_of_questions is optional; if provided, must be positive int
		limit_val = None
		if number_of_questions not in (None, ""):
			try:
				limit_val = int(number_of_questions)
			except (TypeError, ValueError):
				errors['number_of_questions'] = ["Must be an integer."]
			else:
				if limit_val <= 0:
					errors['number_of_questions'] = ["Must be greater than 0."]
		if errors:
			return Response(errors, status=status.HTTP_400_BAD_REQUEST)

		# Convert length to string for database comparison
		length_str = str(length_of_question)

		# Step 1: Query core_question table to pick questions based on parameters
		base_select = (
			"SELECT \"Serial\", \"A\", \"B\", \"C\", \"D\", \"E\", \"F\", \"G\", \"H\", \"I\", \"J\", "
			"\"K\", \"L\", \"M\", \"N\", \"O\", \"P\", \"Q\", \"R\", \"S\", \"T\", \"ANSWER\", \"Complexity\", \"Length\" "
			"FROM core_question_orm WHERE \"Complexity\" = %s AND \"Length\" = %s ORDER BY \"Serial\""
		)

		with connection.cursor() as cursor:
			params = [concept, length_str]
			if limit_val is not None:
				query = base_select + " LIMIT %s"
				params.append(limit_val)
			else:
				query = base_select
			
			cursor.execute(query, params)
			rows = cursor.fetchall()
			
			if not rows:
				return Response({"detail": "No matching questions found"}, status=status.HTTP_400_BAD_REQUEST)

			# Step 2: Insert selected questions into core_assignedquestion table
			insert_sql = (
				"INSERT INTO core_assignedquestion ("
				"serial, a, b, c, d, e, f, g, h, i, j, "
				"k, l, m, n, o, p, q, r, s, t, "
				"answer, complexity, length, student_id, teacher_id, activity_name"
				") VALUES ("
				"%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
				"%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
				"%s, %s, %s, %s, %s, %s"
				")"
			)

			# Insert each selected question with the new parameters
			for row in rows:
				# Add the new parameters to each row (use None if not provided)
				row_with_params = row + (student_id or None, teacher_id or None, activity_name or None)
				cursor.execute(insert_sql, row_with_params)

			# Step 3: Return the assigned questions
			# Build WHERE clause based on provided parameters
			where_conditions = ["complexity = %s", "length = %s"]
			where_params = [concept, length_str]
			
			if student_id:
				where_conditions.append("student_id = %s")
				where_params.append(student_id)
			if teacher_id:
				where_conditions.append("teacher_id = %s")
				where_params.append(teacher_id)
			if activity_name:
				where_conditions.append("activity_name = %s")
				where_params.append(activity_name)
			
			where_clause = " AND ".join(where_conditions)
			
			cursor.execute(
				f"SELECT serial, a, b, c, d, e, f, g, h, i, j, "
				f"k, l, m, n, o, p, q, r, s, t, "
				f"answer, complexity, length, student_id, teacher_id, activity_name "
				f"FROM core_assignedquestion WHERE {where_clause} ORDER BY serial",
				where_params
			)
			assigned_rows = cursor.fetchall()
			
			cols = [
				"serial", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j",
				"k", "l", "m", "n", "o", "p", "q", "r", "s", "t",
				"answer", "complexity", "length", "student_id", "teacher_id", "activity_name"
			]
			assigned_data = [dict(zip(cols, row)) for row in assigned_rows]

		return Response({
			"message": f"Successfully assigned {len(rows)} questions",
			"assigned_questions": assigned_data
		}, status=status.HTTP_201_CREATED)


class AssignLegacyDirectView(APIView):
	permission_classes = [AllowAny]
	def post(self, request):
		concept = request.data.get('concept')
		length_of_question = request.data.get('length_of_question')
		number_of_questions = request.data.get('number_of_questions')

		errors = {}
		if not concept:
			errors['concept'] = ["This field is required."]
		if length_of_question in (None, ""):
			errors['length_of_question'] = ["This field is required."]
		try:
			limit_val = int(number_of_questions) if number_of_questions not in (None, "") else None
		except (TypeError, ValueError):
			errors['number_of_questions'] = ["Must be an integer if provided."]
		if errors:
			return Response(errors, status=status.HTTP_400_BAD_REQUEST)

		length_str = str(length_of_question)

		# Copy rows from core_question_orm to core_assignedquestion with identical legacy columns only
		# Avoid inserting duplicates for the same Complexity/Length by excluding Serial already present
		insert_sql = (
			"INSERT INTO core_assignedquestion (\n"
			"  serial, a, b, c, d, e, f, g, h, i, j,\n"
			"  k, l, m, n, o, p, q, r, s, t,\n"
			"  answer, complexity, length\n"
			")\n"
			"SELECT \n"
			"  q.\"Serial\", q.\"A\", q.\"B\", q.\"C\", q.\"D\", q.\"E\", q.\"F\", q.\"G\", q.\"H\", q.\"I\", q.\"J\",\n"
			"  q.\"K\", q.\"L\", q.\"M\", q.\"N\", q.\"O\", q.\"P\", q.\"Q\", q.\"R\", q.\"S\", q.\"T\",\n"
			"  q.\"ANSWER\", q.\"Complexity\", q.\"Length\"\n"
			"FROM core_question_orm q\n"
			"WHERE q.\"Complexity\" = %s AND q.\"Length\" = %s\n"
			"AND q.\"Serial\" NOT IN (\n"
			"  SELECT serial FROM core_assignedquestion a\n"
			"  WHERE a.complexity = %s AND a.length = %s\n"
			")\n"
			"ORDER BY q.\"Serial\""
		)
		params = [concept, length_str, concept, length_str]
		if limit_val is not None:
			insert_sql += " LIMIT %s"
			params.append(limit_val)

		with connection.cursor() as cursor:
			cursor.execute(
				"SELECT COUNT(*) FROM core_assignedquestion WHERE complexity = %s AND length = %s",
				[concept, length_str],
			)
			before_count = cursor.fetchone()[0]
			cursor.execute(insert_sql, params)
			cursor.execute(
				"SELECT COUNT(*) FROM core_assignedquestion WHERE complexity = %s AND length = %s",
				[concept, length_str],
			)
			after_count = cursor.fetchone()[0]
			inserted = max(after_count - before_count, 0)

		return Response({"inserted": inserted}, status=status.HTTP_201_CREATED)


class AuthLoginView(APIView):
	permission_classes = [AllowAny]
	
	def post(self, request):
		username = request.data.get('username')
		password = request.data.get('password')
		
		if not username or not password:
			return Response({
				"error": "Username and password are required"
			}, status=status.HTTP_400_BAD_REQUEST)
		
		# Authenticate user
		user = authenticate(username=username, password=password)
		
		if user is not None:
			return Response({
				"message": "Login successful",
				"user": {
					"id": user.id,
					"username": user.username,
					"email": user.email,
					"is_staff": user.is_staff
				}
			}, status=status.HTTP_200_OK)
		else:
			return Response({
				"error": "Invalid username or password"
			}, status=status.HTTP_401_UNAUTHORIZED)


class StudentsListView(APIView):
	permission_classes = [AllowAny]
	
	def get(self, request):
		# Get all users who are not staff (students)
		students = User.objects.filter(is_staff=False).values('id', 'username', 'email')
		student_list = list(students)
		
		return Response({
			"students": student_list,
			"total_count": len(student_list)
		})


class SectionsListView(APIView):
	permission_classes = [AllowAny]
	
	def get(self, request):
		# For now, return mock sections. You can replace this with actual section data
		sections = [
			{"id": 1, "name": "Section A", "description": "Beginner Level"},
			{"id": 2, "name": "Section B", "description": "Intermediate Level"},
			{"id": 3, "name": "Section C", "description": "Advanced Level"},
			{"id": 4, "name": "Section D", "description": "Expert Level"}
		]
		
		return Response({
			"sections": sections,
			"total_count": len(sections)
		})


class ComplexityListView(APIView):
	permission_classes = [AllowAny]
	
	def get(self, request):
		# Get all unique complexity values from core_question table
		with connection.cursor() as cursor:
			cursor.execute("SELECT DISTINCT \"Complexity\" FROM core_question ORDER BY \"Complexity\"")
			rows = cursor.fetchall()
			complexities = [{"id": idx + 1, "name": row[0]} for idx, row in enumerate(rows)]
		
		return Response({
			"complexities": complexities,
			"total_count": len(complexities)
		})

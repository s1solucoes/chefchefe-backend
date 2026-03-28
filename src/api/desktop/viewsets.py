from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework import serializers
from rest_framework.response import Response
from apps.academy.models import ConexaTest, ConexaTestStudentResult, Enrollment, Student, StudentChengePasswordToken, Subject
from .serializers import StudentDetailSerializer, StudentLoginSerializer, CourseSerializer, CourseModuleSerializer, SubjectSerializer, StudentRequestTokenSerializer, ValidatedChangePasswordSerializer, MentorshipSerializer, MentorshipSessionSerializer
from apps.course.models import Course, CourseModule
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from apps.mentorship.models import Mentorship, MentorshipSession
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from rest_framework.exceptions import ValidationError
import requests
class StudentLoginViewSet(ViewSet):
    serializer_class = StudentLoginSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = StudentLoginSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except serializers.ValidationError as e:
            # if detail is an array
            if isinstance(e.detail, list):
                return Response({"detail": e.detail[0]}, status=400)
            return Response(e.detail, status=400)
        return Response(serializer.data)
    
class StudentDetailViewSet(ModelViewSet):
    serializer_class = StudentDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'head', 'options']
    queryset = Student.objects.all()
        
    def list(self, request, *args, **kwargs):
        student_id = request.query_params.get('student_id', None)
        if not student_id:
            return Response({"detail": "O parâmetro 'student_id' é obrigatório."}, status=401)
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({"detail": "Estudante não encontrado."}, status=404)
        
        serializer = self.get_serializer(student)
        return Response(serializer.data)
    
class StudentRequestTokenViewSet(ViewSet):
    serializer_class = StudentRequestTokenSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = StudentRequestTokenSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except serializers.ValidationError as e:
            # if detail is an array
            if isinstance(e.detail, list):
                return Response({"detail": e.detail[0]}, status=400)
            return Response(e.detail, status=400)
        return Response({"detail": "Token de alteração de senha enviado para o email cadastrado."})
    
class VerifyTokenViewSet(ViewSet):
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        token_id = request.query_params.get('token', None)
        if not token_id:
            return Response({"detail": "O parâmetro 'token' é obrigatório."}, status=400)
        try:
            token = StudentChengePasswordToken.objects.get(id=token_id)
            if token.expires_at < timezone.now():
                return Response({"detail": "Token inválido ou expirado"}, status=400)
        except StudentChengePasswordToken.DoesNotExist:
            return Response({"detail": "Token inválido ou expirado"}, status=400)
        return Response({"detail": "Token válido."})
    
class ValidatedChangePasswordViewSet(ViewSet):
    serializer_class = ValidatedChangePasswordSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = ValidatedChangePasswordSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except serializers.ValidationError as e:
            # if detail is an array
            if isinstance(e.detail, list):
                return Response({"detail": e.detail[0]}, status=400)
            return Response(e.detail, status=400)
        return Response({"detail": "Senha alterada com sucesso."})
    

class CourseFilter(filters.FilterSet):
    student = filters.UUIDFilter(method='filter_by_student', label='Filtrar por estudante')

    class Meta:
        model = Course
        fields = ['student', 'just_material']

    def filter_by_student(self, queryset, name, value):
        if not value:
            return queryset.none()
        try:
            student = Student.objects.get(id=value)
        except Student.DoesNotExist:
            return queryset.none()
        student_plans = student.enrollments.filter(status='active').values_list('plan', flat=True)
        if student_plans.exists():
            return queryset.filter(plans__in=student_plans).distinct()
        return queryset.none()

class CourseViewSet(ModelViewSet):
    serializer_class = CourseSerializer
    filterset_class = CourseFilter
    filter_backends = [DjangoFilterBackend]
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'head', 'options']
    pagination_class = None  # Desabilita paginação

    def get_queryset(self):
        student_id = self.request.query_params.get('student', None)
        queryset = Course.objects.all()
        if student_id:
            try:
                student = Student.objects.get(id=student_id)
                plans = student.enrollments.filter(status='active').values_list('plan', flat=True)
                return queryset.filter(Q(plans__in=plans) | Q(plans__isnull=True)).distinct()
            except Student.DoesNotExist:
                return Course.objects.none()
        return Course.objects.none()
    

    def list(self, request, *args, **kwargs):
        student_id = request.query_params.get('student', None)
        if not student_id:
            return Response({"detail": "O parâmetro 'student' é obrigatório."}, status=401)
        return super().list(request, *args, **kwargs)
    

class courseModuleFilter(filters.FilterSet):
    subject = filters.CharFilter(method='filter_by_subject', label='Filtrar por matéria')
    course = filters.CharFilter(field_name='course__slug', lookup_expr='iexact')

    class Meta:
        model = CourseModule
        fields = ['subject', 'course']

    def filter_by_subject(self, queryset, name, value):
        if not value:
            return queryset
        if value.lower() == 'aulas':
            return queryset.filter()
        return queryset.filter(
            subject__slug__iexact=value
        )

class CourseModuleViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = CourseModuleSerializer
    pagination_class = None  # Desabilita paginação
    http_method_names = ['get', 'head', 'options']
    filter_backends = [DjangoFilterBackend]
    filterset_class = courseModuleFilter
    def get_queryset(self):
        return CourseModule.objects.all()
    

class CourseSubjectsViewSet(ViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    def list(self, request, *args, **kwargs):
        course_slug = request.query_params.get('course', None)
        if not course_slug:
            return Response({"detail": "O parâmetro 'course' é obrigatório."}, status=401)
        try:
            course = Course.objects.get(slug=course_slug)
        except Course.DoesNotExist:
            return Response({"detail": "Curso não encontrado."}, status=404)
        
        subjects = Subject.objects.filter(course_modules__course__id=course.id).order_by('position', 'name').distinct()
        serializer = SubjectSerializer(subjects, many=True)
        return Response(serializer.data)
    
        

class MentorshipViewSet(ModelViewSet):
    serializer_class = MentorshipSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    http_method_names = ['get', 'head', 'options']

    def get_queryset(self):
        student_id = self.request.query_params.get('student_id', None)
        queryset = Mentorship.objects.filter(end_time__gte=timezone.now()).exclude(status__in=['completed', 'canceled'])
        if student_id:
            try:
                student = Student.objects.get(id=student_id)
                plans = student.enrollments.filter(status='active').values_list('plan', flat=True)
                return queryset.filter(plans__in=plans).distinct()
            except Student.DoesNotExist:
                return Mentorship.objects.none()
        return Mentorship.objects.none()
    
    def list(self, request, *args, **kwargs):
        student_id = request.query_params.get('student_id', None)
        if not student_id:
            return Response({"detail": "O parâmetro 'student_id' é obrigatório."}, status=401)
        return super().list(request, *args, **kwargs)
    

class MentorshipSessionViewSet(ModelViewSet):
    serializer_class = MentorshipSessionSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    http_method_names = ['get', 'head', 'options', 'post']

    def get_queryset(self):
        student_id = self.request.query_params.get('student_id', None)
        queryset = MentorshipSession.objects.all()
        if student_id:
            try:
                student = Student.objects.get(id=student_id)
                return queryset.filter(student=student)
            except Student.DoesNotExist:
                return MentorshipSession.objects.none()
        return MentorshipSession.objects.none()
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        mentorship_id = request.data.get('mentorship', None)
        student_id = request.data.get('student', None)
        if not mentorship_id or not student_id:
            return Response({"detail": "Os parâmetros 'mentorship' e 'student' são obrigatórios."}, status=400)
        try:
            MentorshipSession.objects.get(mentorship_id=mentorship_id, student_id=student_id)
            return Response({"detail": "Já existe uma sessão para este estudante e mentoria."}, status=400)
        except MentorshipSession.DoesNotExist:
            try:
                return super().create(request, *args, **kwargs)
            except ValidationError as e:
                return Response({"detail": e.detail[0] if e.detail else "Erro de validação."}, status=400)
            except Exception as e:
                return Response({"detail": str(e)}, status=400)

    def list(self, request, *args, **kwargs):
        student_id = request.query_params.get('student_id', None)
        if not student_id:
            return Response({"detail": "O parâmetro 'student_id' é obrigatório."}, status=401)
        return super().list(request, *args, **kwargs)


class GetOldTokenViewSet(ViewSet):
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        student_id = request.query_params.get('student_id', None)
        if not student_id:
            return Response({"detail": "O parâmetro 'student_id' é obrigatório."}, status=401)
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({"detail": "Estudante não encontrado."}, status=404)
        
        email = student.email
        plans = student.enrollments.filter(status='active').values_list('plan__slug', flat=True)
        response = requests.post("https://plataforma-paulinho-production.up.railway.app/api/v1/student/login-token/",
                                    json={"email": email, "name": student.name, "plans": list(plans)})
        if response.status_code != 201:
            print(response.text)
            return Response({"detail": "Erro ao obter token antigo."}, status=500)
        
        data = response.json()
        return Response({
            "token": data.get("access_token"), 
            "url": "https://painelgenial.vercel.app/redirect?token=" + data.get("access_token"),
            "email": email,
            "name": student.name,
            "plans": list(plans)
        })
    
    


class TestResultViewSet(ViewSet):
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        test_id = request.query_params.get('id', None)
        student_id = request.query_params.get('student_id', None)
        if not test_id:
            return Response({"detail": "O parâmetro 'id' é obrigatório."}, status=401)
        if not student_id:
            return Response({"detail": "O parâmetro 'student_id' é obrigatório."}, status=401)
        try:
            test = ConexaTest.objects.get(id=test_id)
        except ConexaTest.DoesNotExist:
            return Response({"detail": "Teste não encontrado."}, status=404)
        
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({"detail": "Estudante não encontrado."}, status=404)
        enrollments_numbers = student.enrollments.filter().values_list('number', flat=True)

        data = {
            "id": test.id,
            "test": test.name,
            "cover": test.cover.file.url if test.cover else None,
            "student_id": student_id,
            "student_name": student.name,
        }
        success = False
        for r in test.result:
            if r.get("MATRICULA") in enrollments_numbers:
                result, _ = ConexaTestStudentResult.objects.get_or_create(student=student, test=test, defaults={"result": r})
                if not _:
                    result.result = r
                    result.save()
                data["result"] = r
                success = True
                break
        if not success:
            return Response({"detail": "Resultado não encontrado."}, status=404)
        return Response(data)
    

class ConextaTestViewSet(ViewSet):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [AllowAny]
    def list(self, request, *args, **kwargs):
        tests = ConexaTest.objects.filter(is_active=True).order_by('position', 'name')
        data = []
        for test in tests:
            data.append({
                "id": test.id,
                "name": test.name,
                "cover": test.cover.file.url if test.cover else None,
                "description": test.description,
            })
        return Response(data)
    

class IndicationViewSet(ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Student.objects.filter(code__isnull=False).order_by('name')
    http_method_names = ['get', 'head', 'options']
    def list(self, request, *args, **kwargs):
        return Response({"detail": "O parâmetro 'code' é obrigatório."}, status=400)
    def retrieve(self, request, *args, **kwargs):
        code = kwargs.get('pk', None)
        if not code:
            return Response({"detail": "O parâmetro 'code' é obrigatório."}, status=400)
        try:
            student = Student.objects.get(code=code)
            # redirect to url with token
            response = {
                "email": student.email,
                "name": student.name,
            }
            return Response(response)
        except Student.DoesNotExist:
            return Response({"detail": "Código de indicação inválido."}, status=404)
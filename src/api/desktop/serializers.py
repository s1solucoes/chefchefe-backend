from rest_framework import serializers
from apps.academy.models import Student, StudentChengePasswordToken, Subject, Enrollment, CreditTransaction, CreditsTypesChoices
from apps.course.models import Course, CourseModule, CourseLesson, Attachment
from apps.mentorship.models import Mentorship, MentorshipSession
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.db.models import Q
from django.db import transaction

class EnrollmentSerializer(serializers.ModelSerializer):
    plan_name = serializers.ReadOnlyField(source='plan.name')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    plan_slug = serializers.ReadOnlyField(source='plan.slug')
    class Meta:
        model = Enrollment
        fields = [
            'id',
            'plan_name',
            'status',
            'status_display',
            'start_date',
            'end_date',
            'number',
            'plan',
            'plan_slug'
        ]

class StudentLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    name = serializers.ReadOnlyField(source='student.name')
    id = serializers.ReadOnlyField(source='student.id')
    enrollments = EnrollmentSerializer(source='student.enrollments', many=True, read_only=True)
    mentorship_credits = serializers.ReadOnlyField(source='student.mentorship_credits')
    class Meta:
        fields = ['email', 'password', 'name', 'id', 'enrollments', 'mentorship_credits']

    def create(self, validated_data):
        email = validated_data.get('email')
        password = validated_data.get('password')

        if not email or not password:
            raise serializers.ValidationError(detail="Email e senha são obrigatórios")

        try:
            student = Student.objects.get(email=email)
            if not check_password(password, student.password):
                raise serializers.ValidationError(detail="Credenciais inválidas")
        except Student.DoesNotExist:
            raise serializers.ValidationError(detail="Credenciais inválidas")
        


        validated_data['student'] = student
        return validated_data
    
class StudentDetailSerializer(serializers.ModelSerializer):
    enrollments = EnrollmentSerializer(many=True, read_only=True)
    mentorship_credits = serializers.ReadOnlyField()
    class Meta:
        model = Student
        fields = [
            'id',
            'name',
            'email',
            'enrollments',
            'mentorship_credits',
            'code',
        ]
    

class StudentRequestTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    class Meta:
        fields = ['email']


    def create(self, validated_data):
        email = validated_data.get('email')
        try:
            student = Student.objects.get(email=email)
            token, _ = StudentChengePasswordToken.objects.get_or_create(student=student)
            if not _ and token.expires_at < timezone.now():
                token.delete()
                token = StudentChengePasswordToken.objects.create(student=student)
            token.update_expires_at()
            if not token.sended_at or token.sended_at < timezone.now() - timezone.timedelta(minutes=3):
                token.send_email()
        except Student.DoesNotExist:
            pass
        return validated_data
    
class ValidatedChangePasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True)
    class Meta:
        fields = ['token', 'new_password']
    
    def create(self, validated_data):
        token_id = validated_data.get('token')
        new_password = validated_data.get('new_password')
        try:
            token = StudentChengePasswordToken.objects.get(id=token_id)
            if token.expires_at < timezone.now():
                raise serializers.ValidationError(detail="Token inválido ou expirado")
            student = token.student
            student.password = make_password(new_password)
            student.save()
            token.delete()
        except StudentChengePasswordToken.DoesNotExist:
            raise serializers.ValidationError(detail="Token inválido ou expirado")
        return validated_data
    


class CourseSerializer(serializers.ModelSerializer):
    cover_url = serializers.URLField(source='cover.file.url', read_only=True)
    class Meta:
        model = Course
        fields = '__all__'

class AttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.URLField(source='file.file.url', read_only=True)
    class Meta:
        model = Attachment
        fields = [
            'id',
            'file_url',
            'link',
            'title',
        ]

class CourseLessonSerializer(serializers.ModelSerializer):
    content_url = serializers.URLField(source='content.file.url', read_only=True)
    content_type = serializers.CharField(source='content.type', read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    class Meta:
        model = CourseLesson
        fields = [
            'id',
            'position',
            'title',
            'module',
            'video_url',
            'content_type',
            'content_url',
            'attachments',
        ]

class CourseModuleSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = CourseModule
        fields = [
            'id',
            'position',
            'title',
            'description',
            'course',
            'subject',
            'lessons',
        ]

    def get_lessons(self, obj):
        student_id = self.context['request'].query_params.get('student_id', None)
        lessons = obj.lessons.filter(Q(student_groups__members__id=student_id) | Q(student_groups__isnull=True)).distinct()
        return CourseLessonSerializer(lessons, many=True).data
    


class SubjectSerializer(serializers.ModelSerializer):
    cover_url = serializers.URLField(source='cover.file.url', read_only=True)
    class Meta:
        model = Subject
        fields = [
            'id',
            'name',
            'slug',
            'position',
            'cover_url',
        ]


class MentorshipSessionSerializer(serializers.ModelSerializer):
    status_display = serializers.ReadOnlyField(source='get_status_display')
    class Meta:
        model = MentorshipSession
        fields = '__all__'
        read_only_fields = ['status', 'position', 'credits_transaction', 'credits_used']

    @transaction.atomic
    def create(self, validated_data):
        mentorship = validated_data.get('mentorship')
        existing_sessions = MentorshipSession.objects.filter(mentorship=mentorship, position__gt=0).count()
        validated_data['position'] = existing_sessions + 1
        if mentorship.pricing > 0:
            try:
                transaction = CreditTransaction.objects.create(
                    student=validated_data['student'],
                    type=CreditsTypesChoices.MENTORSHIP,
                    amount=-mentorship.pricing,
                    description=f"Crédito debitado para sessão de mentoria: {mentorship.title}",
                    status=CreditTransaction.CreditStatusChoices.PENDING
                )
            except Exception as e:
                raise serializers.ValidationError(f"Erro ao criar transação de crédito: {str(e)}")
            validated_data['credits_transaction'] = transaction
            try:
                session = super().create(validated_data)
            except Exception as e:
                raise serializers.ValidationError(f"Erro ao criar sessão de mentoria: {str(e)}")
            transaction.status = CreditTransaction.CreditStatusChoices.APPROVED
            try:
                transaction.save()
            except Exception as e:
                raise serializers.ValidationError(f"Erro ao atualizar transação de crédito: {str(e)}")
            return session
        return super().create(validated_data)
class MentorshipSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.get_full_name')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    session = serializers.SerializerMethodField()
    allowed = serializers.SerializerMethodField()
    class Meta:
        model = Mentorship
        fields = [
            'id',
            'title',
            'start_time',
            'end_time',
            'status',
            'teacher_name',
            'status_display',
            'session',
            'url',
            'pricing',
            'allowed',
        ]

    def get_allowed(self, obj):
        student_id = self.context['request'].query_params.get('student_id', None)
        if not student_id:
            return False
        try:
            student = Student.objects.get(id=student_id)
            if student.mentorship_credits >= obj.pricing:
                return True
            return False
        except Student.DoesNotExist:
            return False

    def get_session(self, obj):
        student_id = self.context['request'].query_params.get('student_id', None)
        try:
            session = MentorshipSession.objects.get(mentorship=obj, student_id=student_id)
            return MentorshipSessionSerializer(session).data
        except MentorshipSession.DoesNotExist:
            return None


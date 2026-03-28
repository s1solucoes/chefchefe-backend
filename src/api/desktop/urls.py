from rest_framework.routers import DefaultRouter
from .viewsets import (
    StudentLoginViewSet, 
    CourseViewSet, 
    CourseModuleViewSet, 
    CourseSubjectsViewSet, 
    StudentRequestTokenViewSet, 
    ValidatedChangePasswordViewSet, 
    VerifyTokenViewSet, 
    MentorshipViewSet, 
    MentorshipSessionViewSet, 
    GetOldTokenViewSet, 
    StudentDetailViewSet, 
    TestResultViewSet,
    ConextaTestViewSet,
    IndicationViewSet
)
router = DefaultRouter()
router.register("login", StudentLoginViewSet, basename="studentlogin")
router.register("request-change-password-token", StudentRequestTokenViewSet, basename="studentrequestchangepasswordtoken")
router.register("validated-change-password", ValidatedChangePasswordViewSet, basename="validatedchangepassword")
router.register("verify-password-token", VerifyTokenViewSet, basename="verifytoken")
router.register("courses", CourseViewSet, basename="course")
router.register("course-subjects", CourseSubjectsViewSet, basename="coursesubject")
router.register("course-modules", CourseModuleViewSet, basename="coursemodule")
router.register("mentorships", MentorshipViewSet, basename="mentorship")
router.register("mentorship-sessions", MentorshipSessionViewSet, basename="mentorshipsession")
router.register("get-old-token", GetOldTokenViewSet, basename="getoldtoken")
router.register("student-details", StudentDetailViewSet, basename="studentdetail")
router.register("conexatest", TestResultViewSet, basename="conexatest")
router.register("conexa-test", ConextaTestViewSet, basename="conexatestlist")
router.register("indications", IndicationViewSet, basename="indication")

urlpatterns = router.urls

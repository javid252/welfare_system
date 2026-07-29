from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("employees", views.EmployeeViewSet, basename="employee")
router.register("services", views.ServiceCatalogViewSet, basename="service")
router.register("activities", views.ActivityViewSet, basename="activity")
router.register("tasks", views.TaskAssignmentViewSet, basename="task")
router.register("holidays", views.HolidayViewSet, basename="holiday")
router.register("budgets", views.WelfareYearlyBudgetViewSet, basename="budget")
router.register("distribution", views.WelfareDistributionViewSet, basename="distribution")

urlpatterns = [
    # Auth
    path("auth/login/", views.LoginAPIView.as_view(), name="api-login"),
    path("auth/logout/", views.LogoutAPIView.as_view(), name="api-logout"),
    path("auth/profile/", views.ProfileAPIView.as_view(), name="api-profile"),

    # Dashboard aggregation
    path("dashboard/employee-summary/", views.EmployeeSummaryView.as_view(), name="dashboard-employee-summary"),
    path("dashboard/team-performance/", views.TeamPerformanceView.as_view(), name="dashboard-team-performance"),
    path("dashboard/province-heatmap/", views.ProvinceHeatmapView.as_view(), name="dashboard-province-heatmap"),
    path("dashboard/trends/", views.TrendsView.as_view(), name="dashboard-trends"),

    # CRUD + audits (audits are actions nested under activities, e.g.
    # /api/activities/<id>/submit-audit/ and /api/activities/audit-queue/)
    path("", include(router.urls)),
]

"""
Template (page-shell) views.

Per the project's frontend approach, Vue 2 components are embedded inside
Django templates rather than building a full SPA. These views therefore do
very little: they authenticate the user and render the right template with
minimal context (mostly role flags for showing/hiding sidebar sections). All
actual data (activities, dashboards, charts) is fetched client-side from the
DRF API in `api/`.
"""

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect

from .permissions import is_admin, is_supervisor_or_above


def login_view(request):
    """Simple session-based login. Vue handles client-side field validation;
    Django handles the actual authentication + session creation."""
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("core:dashboard")
        messages.error(request, "نام کاربری یا رمز عبور نادرست است.")

    return render(request, "login.html")


@login_required(login_url="core:login")
def logout_view(request):
    logout(request)
    return redirect("core:login")


@login_required(login_url="core:login")
def dashboard_view(request):
    """
    Renders the single dashboard shell. The actual content area is populated
    by Vue Router based on the employee's role (see static/js/app.js).
    """
    context = {
        "employee": request.user,
        "is_admin": is_admin(request.user),
        "is_supervisor_or_above": is_supervisor_or_above(request.user),
        "role": request.user.role,
    }
    return render(request, "dashboard.html", context)

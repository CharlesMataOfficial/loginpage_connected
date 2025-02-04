# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.urls import reverse
from .models import CustomUser
from django.views.decorators.cache import never_cache

@never_cache
def login_view(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        pin = request.POST.get('pin')

        try:
            # Try to retrieve the user by employee_id.
            user = CustomUser.objects.get(employee_id=employee_id)
        except CustomUser.DoesNotExist:
            # If no user is found, return a specific error.
            return render(request, 'index.html', {'error': 'Employee ID not found'})

        # Check if the PIN is correct.
        if user.pin != pin:
            return render(request, 'index.html', {'error': 'Incorrect PIN'})

        # If both are correct, log the user in.
        login(request, user)

        # Redirect based on user type.
        if user.is_staff or user.is_superuser:
            return redirect(reverse('admin:index'))  # Admin dashboard
        else:
            return redirect('user_page')  # Regular user page

    return render(request, 'index.html')

def user_page(request):
    return render(request, 'user_page.html')

def logout_view(request):
    logout(request)  # Logs out the user
    return redirect('login')  # Redirects to the login page


import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import TimeEntry

@require_POST
def clock_in_view(request):
    data = json.loads(request.body)
    employee_id = data.get('employee_id')
    pin = data.get('pin')

    try:
        user = CustomUser.objects.get(employee_id=employee_id)
    except CustomUser.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Employee ID not found'})

    if user.pin != pin:
        return JsonResponse({'success': False, 'error': 'Incorrect PIN'})

    # Use the clock_in classmethod from TimeEntry to create a new time entry.
    entry = TimeEntry.clock_in(user)
    time_in_formatted = timezone.localtime(entry.time_in).strftime("%I:%M %p, %B %d, %Y")

    # For clock in, time_out is not yet set (so null)
    return JsonResponse({
        'success': True,
        'employee_id': user.employee_id,
        'first_name': user.first_name,
        'surname': user.surname,
        'company': user.company,
        'time_in': time_in_formatted,
        'time_out': None
    })

@require_POST
def clock_out_view(request):
    data = json.loads(request.body)
    employee_id = data.get('employee_id')
    pin = data.get('pin')

    try:
        user = CustomUser.objects.get(employee_id=employee_id)
    except CustomUser.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Employee ID not found'})

    if user.pin != pin:
        return JsonResponse({'success': False, 'error': 'Incorrect PIN'})

    try:
        # Get the most recent open time entry for the user and clock it out.
        open_entry = TimeEntry.objects.filter(user=user, time_out__isnull=True).latest('time_in')
        open_entry.clock_out()
    except TimeEntry.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'No active clock in found.'})

    time_in_formatted = timezone.localtime(open_entry.time_in).strftime("%I:%M %p, %B %d, %Y")
    time_out_formatted = timezone.localtime(open_entry.time_out).strftime("%I:%M %p, %B %d, %Y")

    return JsonResponse({
        'success': True,
        'employee_id': user.employee_id,
        'first_name': user.first_name,
        'surname': user.surname,
        'company': user.company,
        'time_in': time_in_formatted,
        'time_out': time_out_formatted
    })

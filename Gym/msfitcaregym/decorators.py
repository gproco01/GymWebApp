from django.http import HttpResponse
from django.shortcuts import redirect

from . import models
from .models import User
def unauthenticated_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('msfitcaregym:home')
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_func

def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            group = None
            if request.user.groups.exists():
                group = request.user.groups.all()[0].name
            if group in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                return redirect('msfitcaregym:home')
        return wrapper_func
    return decorator

def registration_completed():
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            try:
                userProfile = models.UserProfile.objects.get(user=request.user)
            except models.UserProfile.DoesNotExist:
                if request.user.groups.exists():
                    group = request.user.groups.all()[0].name
                    if group =='admin':
                        return view_func(request, *args, **kwargs)
                else:
                    return redirect('msfitcaregym:registrationform')
            if userProfile.approve != True:
                return redirect('msfitcaregym:registrationform')
            else:
                return view_func(request, *args, **kwargs)
        return wrapper_func
    return decorator
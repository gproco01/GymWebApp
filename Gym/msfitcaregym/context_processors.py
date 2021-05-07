from . import models

def announcement_processor(request):
    if request.user.is_authenticated:
        if request.user.groups.exists():
            group = request.user.groups.all()[0].name
            if group == 'admin':
               msgs = None
               total = 0
               try:
                   request_users = models.UserProfile.objects.filter(accountStatus = 'Request').count()
               except:
                   request_users = 0
        else:
            request_users = 0
            try:
                user = models.UserProfile.objects.get(user = request.user)
                msgs = models.Announcements.objects.filter(submited_date__gt = user.checkann)
                total = msgs.count()
            except:
                msgs = models.Announcements.objects.all().order_by('-submited_date')[:3]
                total = msgs.count()
    else:
        request_users = 0
        msgs = None
        total = 0
    return {
        'msgs' : msgs,
        'total':total,
        'req_total':request_users
    }

def reservations_processor(request):
    if request.user.is_authenticated:
        types=models.Type.objects.filter(active=True)
    else:
        types=None
    print(types)
    return {
        'types' : types,
    }
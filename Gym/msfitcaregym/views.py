import json
import random
import string
from datetime import datetime, timedelta, date

import pytz
from django.db import connection


from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core import serializers
from django.core.mail import send_mail, BadHeaderError
from django.db.models import Q
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.generic.edit import CreateView
from django.contrib.auth.models import Group

from . import forms, models
from django.urls import reverse
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, AuthenticationForm

# Create your views here.
from .decorators import allowed_users, registration_completed
from django.core.mail import send_mail
from django.conf import settings


def index(request):

    try:
        hometext = models.HomePageText.objects.all()[0]
    except:
        hometext = None
    form = forms.HomePageForm(request.POST or None,instance=hometext)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('msfitcaregym:home'))
    context = {
        'hometext':hometext,
        'tab': 'home',
        'form':form
    }
    return render(request, 'msfitcaregym/home.html', context)


@login_required()
@registration_completed()
def dashboard(request):
    tz_CY = pytz.timezone('Europe/Athens')
    user = request.user
    userprof = models.UserProfile.objects.get(user=user)
    reservations = models.GymReservations.objects.filter(user=userprof, date__gte=datetime.today()).order_by('date')[:5]
    if reservations.count() == 1:
        next = reservations[0]
        if next.date == datetime.today().date() and datetime.now(tz_CY).time() > next.time.start_time:
            next = "Δεν υπάρχει κάποια κράτηση"
            reservations = None
    elif reservations.count() > 1:
        next = reservations[0]
        if next.date == datetime.today().date() and datetime.now(tz_CY).time() > next.time.start_time:
            next = reservations[1]
            reservations = models.GymReservations.objects.filter(user=userprof, date__gte=datetime.today()).order_by('date')[1:5]
    else:
        next = "Δεν υπάρχει κάποια κράτηση"
    try:
        payment = models.Payments.objects.filter(user=userprof).latest('pay_until')
        today = datetime.now()
        day = datetime.strptime(payment.pay_until.strftime('%Y%m%d'), '%Y%m%d')
        daysdifference = (today - day).days
        if daysdifference > 0:
            over = True
        else:
            over = False
    except:
        payment = None
        over = "Δεν έχει καταχωρηθεί"

    try:
        allphysios = models.PhysioReservations.objects.filter(user=userprof, date__gte=datetime.today()).order_by('date')
        if allphysios.count() == 1:
            physio = allphysios[0]
            if physio.date == datetime.today().date() and datetime.now(tz_CY).time() > physio.start_time:
                physio = None
        elif allphysios.count() > 1:
            physio = allphysios[0]
            if physio.date == datetime.today().date() and datetime.now(tz_CY).time() > physio.start_time:
                physio = allphysios[1]
    except:
        physio = None
    context = {
        'next': next,
        'payment': payment,
        'over': over,
        'reservations': reservations,
        'physio': physio,
        'tab': 'dash',
    }
    return render(request, 'msfitcaregym/dashboard.html', context)


def Register(request):
    registered = False
    if request.method == 'POST':
        user_form = forms.RegisterForm(data=request.POST)
        if user_form.is_valid():
            user = user_form.save(commit=False)
            user.is_active = False
            user.email = user.username
            user.save()
            userProfile = models.UserProfile(user=user, first_name=user.first_name, last_name=user.last_name)
            userProfile.save()
            registered = True
        else:
            messages.error(request, user_form.errors)
    else:
        user_form = forms.RegisterForm()
    context = {
        'user_form': user_form,
        'registered': registered,
        'tab': 'register'
    }
    return render(request, 'msfitcaregym/register.html', context)


def Login(request):
    # form = AuthenticationForm(data = request.POST or None)
    if request.user.is_authenticated:
        return redirect('msfitcaregym:home')
    else:
        if request.method == 'POST':
            # print(request.POST)
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('msfitcaregym:home')
            else:
                try:
                    user1 = models.User.objects.get(username=username)
                    if user1.is_active:
                        messages.error(request, "Το email ή ο κωδικός είναι λανθασμένα")
                    else:
                        messages.error(request, 'Ο χρήστης δεν είναι ενεργός')
                except Exception as e:
                    print(e)
                    messages.error(request, "Το email ή ο κωδικός είναι λανθασμένα")

        return render(request, 'msfitcaregym/login.html')


@login_required()
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Το συνθηματικό σας έχει αλλάξει με επιτυχία!')
            return redirect('msfitcaregym:change_password')
        else:
            messages.error(request, 'Παρακαλώ διορθώστε το λάθος που αναγράφεται')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'msfitcaregym/change_password.html', {
        'form': form
    })


def password_reset_request(request):
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = models.User.objects.filter(Q(username=data))
            if associated_users.exists():
                for user in associated_users:
                    subject = "Αίτημα για επαναφορά κωδικού πρόσβασης"
                    email_template_name = "password/password_reset_email.txt"
                    c = {
                        "email": user.username,
                        'domain': 'msfitcaregym.com',
                        'site_name': 'MSFitCareGym',
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'http',
                    }
                    email = render_to_string(email_template_name, c)
                    try:
                        send_mail(subject, email, settings.EMAIL_HOST_USER, [user.username], fail_silently=False)
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.')
                    return redirect("/password_reset/done/")
    password_reset_form = PasswordResetForm()
    return render(request=request, template_name="password/password_reset.html",
                  context={"password_reset_form": password_reset_form})


@login_required()
@allowed_users(['admin'])
def adminPhysioCalendar(request):
    # users=models.UserProfile.objects.filter(accountStatus="Accepted")
    users = models.UserProfile.objects.filter(accountStatus__in=['Accepted', 'NoUser'])
    # print("users: ", users)
    context = {
        "users": users
    }

    return render(request, 'msfitcaregym/adminPhysioCalendar.html', context)


@login_required()
@registration_completed()
def userPhysioCalendar(request):
    # # users=models.UserProfile.objects.filter(accountStatus="Accepted")
    # users=models.UserProfile.objects.all()
    # print("users: ",users)
    # context = {
    #     "users":users
    # }

    return render(request, 'msfitcaregym/userPhysioCalendar.html')


@login_required()
@allowed_users(['admin'])
def addPhysioSlot(request):
    date = request.POST.get("date", None)
    # end_date = request.POST.get("end_date", None)
    start_time = request.POST.get("start_time", None)
    end_time = request.POST.get("end_time", None)
    print(request.POST)
    if (date == ""):
        date = None
    if (start_time == ""):
        start_time = None
    if (end_time == ""):
        end_time = None
    if date is not None:
        slot = models.PhysioReservations(date=date, start_time=start_time, end_time=end_time)
        slot.save()
    data = {}
    return JsonResponse(data)


def toArray(events, color=None, title=0):
    # print(events)
    events_array = []
    for event in events:
        # print(event)
        # print("ev ", event)
        event_array = {}
        if title == 1:
            event_array['title'] = str(event.user.first_name) + " " + str(event.user.last_name)
        elif title == 2:
            event_array['title'] = "Η κράτηση μου"
        else:
            event_array['title'] = "Open"
        event_array['id'] = event.id_reservation
        if color is not None:
            event_array['color'] = color
        if event.start_time is None or event.end_time is None:
            event_array['start'] = event.date.strftime("%Y-%m-%d")
            event_array['end'] = event.date.strftime("%Y-%m-%d")
        else:
            event_array['start'] = datetime.combine(event.date, event.start_time).strftime("%Y-%m-%d %H:%M:%S")
            event_array['end'] = datetime.combine(event.date, event.end_time).strftime("%Y-%m-%d %H:%M:%S")

        if event.user is not None:
            event_array['extendedProps'] = {'isReserved': True, 'user_id': event.user_id}

        else:
            event_array['extendedProps'] = {'isReserved': False}

        events_array.append(event_array)
    return events_array


@login_required()
@registration_completed()
def physioSlotsJSON(request):
    """

    :param request:
    :return:
    """
    eventsList = []
    print(request.POST)
    start = request.POST.get("start", None)
    end = request.POST.get("end", None)
    start = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S%z')
    end = datetime.strptime(end, '%Y-%m-%dT%H:%M:%S%z')
    status = request.POST.get("status", None)
    user = request.POST.get("user", None)

    if status == "free":
        if user == 'admin':
            slots = models.PhysioReservations.objects.filter(date__gte=datetime.date(start),
                                                             date__lte=datetime.date(end), user=None)
        else:
            if datetime.date(start) < datetime.date(datetime.today()):
                slots = models.PhysioReservations.objects.filter(date__gte=datetime.today(),
                                                                 date__lte=datetime.date(end), user=None)
            else:
                slots = models.PhysioReservations.objects.filter(date__gte=datetime.date(start),
                                                                 date__lte=datetime.date(end), user=None)
            slots = slots.exclude(date=datetime.today(), start_time__lt=datetime.now().strftime("%H:%M"))
        slotsList = toArray(slots, title=0)
    elif status == "reserved":
        slots = models.PhysioReservations.objects.filter(date__gte=datetime.date(start),
                                                         date__lte=datetime.date(end)).exclude(user=None)
        slotsList = toArray(slots, title=1)
    elif status == "user":
        slots = models.PhysioReservations.objects.filter(date__gte=datetime.date(start), date__lte=datetime.date(end),
                                                         user__user=request.user)
        slotsList = toArray(slots, title=2)

    return JsonResponse(slotsList, safe=False)


@login_required()
@allowed_users(['admin'])
def physioSlotUpdate(request):
    date = request.POST.get("date", None)
    start_time = request.POST.get("start_time", None)
    end_time = request.POST.get("end_time", None)
    id = request.POST.get("id", None)
    if (start_time == ""):
        start_time = None
    if (end_time == ""):
        end_time = None

    slot = models.PhysioReservations.objects.get(id_reservation=id)
    slot.date = date
    slot.start_time = start_time
    slot.end_time = end_time

    slot.save()
    data = {}
    return JsonResponse(data)


@login_required()
@allowed_users(['admin'])
def physioSlotDelete(request):
    id = request.POST.get("id", None)

    slot = models.PhysioReservations.objects.get(id_reservation=id)
    slot.delete()

    data = {}
    return JsonResponse(data)


@login_required()
@allowed_users(['admin'])
def physioAdminRemoveReservation(request):
    id = request.POST.get("id", None)

    slot = models.PhysioReservations.objects.get(id_reservation=id)
    slot.user = None
    slot.save()

    data = {}
    return JsonResponse(data)


@login_required()
@registration_completed()
def physioUserRemoveReservation(request):
    id = request.POST.get("id", None)
    userProfile = models.UserProfile.objects.get(user=request.user)

    slot = models.PhysioReservations.objects.get(id_reservation=id, user=userProfile)
    slot.user = None
    slot.save()

    data = {}
    return JsonResponse(data)


@login_required()
@allowed_users(['admin'])
def physioAdminAddReservation(request):
    id = request.POST.get("id", None)
    user_id = request.POST.get("select_user", None)
    print(request.POST)

    user = models.UserProfile.objects.get(id=user_id)
    slot = models.PhysioReservations.objects.get(id_reservation=id)
    if user and slot:
        slot.user = user
        slot.save()

    return HttpResponseRedirect(reverse('msfitcaregym:adminPhysioCalendar'))


@login_required()
@registration_completed()
def physioUserAddReservation(request):
    id = request.POST.get("id", None)
    userProfile = models.UserProfile.objects.get(user=request.user)

    slot = models.PhysioReservations.objects.get(id_reservation=id)
    if slot.user == None:
        slot.user = userProfile
        slot.save()

    data = {}
    return JsonResponse(data)


@login_required()
@allowed_users(['admin'])
def physioNewCard(request):
    title = request.POST.get('title', None)
    user_id = request.POST.get('user', None)
    card = models.PhysioCard(user_id=user_id, title=title)
    card.save()
    data = {"card_id": card.id_card}
    return JsonResponse(data)


@login_required()
@allowed_users(['admin'])
def userCards(request, pk):
    cards = models.PhysioCard.objects.filter(user_id=pk)
    context = {
        "cards": cards
    }

    return render(request, 'msfitcaregym/userCards.html', context)


@login_required()
@allowed_users(['admin'])
def addSlotsCalendar(request):
    # users=models.UserProfile.objects.filter(accountStatus="Accepted")
    types = models.Type.objects.filter(active=True)
    context = {
        "types": types
    }

    return render(request, 'msfitcaregym/addSlotsCalendar.html', context)


@login_required()
@allowed_users(['admin'])
def addSlots(request):
    slots = json.loads(request.POST.get('events'))
    type = request.POST.get('type', None)
    valid_from = request.POST.get('valid_from', None)
    new_valid_to = request.POST.get('valid_to', None)
    today = date.today()
    if valid_from is None:
        valid_from = today + timedelta(days=5)
    else:
        valid_from = datetime.strptime(valid_from, '%Y-%m-%d')
    # print(valid_from)
    valid_to = valid_from + timedelta(days=-1)
    old_slots = models.Slots.objects.filter(type_id=type, valid_to=None) | models.Slots.objects.filter(type_id=type,
                                                                                                       valid_to__gt=valid_to)
    num = old_slots.count()
    for slot in old_slots:
        slot.valid_to = valid_to
        slot.save()
        reserv = models.GymReservations.objects.filter(type=type, time=slot, date__gt=valid_to).delete()
    # if num>0:
    #     for slot in slots:
    #         day=datetime.strptime(slot['date'],'%Y-%m-%d')
    #         n=models.Slots(day=day.isoweekday(), start_time=slot['start_time'],end_time=slot['end_time'],type_id=type, valid_from=valid_from)
    #         n.save()
    # else:
    for slot in slots:
        day = datetime.strptime(slot['date'], '%Y-%m-%d')
        n = models.Slots(day=day.isoweekday(), start_time=slot['start_time'], end_time=slot['end_time'], type_id=type,
                         valid_from=valid_from, valid_to=new_valid_to)
        n.save()

    data = {}
    return JsonResponse(data)


def slotsToArray(type, day, slots, status, color=None):
    # print(slots)
    events_array = []
    total_persons = models.Type.objects.get(id_type=type).total_persons
    for slot in slots:
        res = models.GymReservations.objects.filter(type_id=type, date=day, time=slot).count()
        my = False
        if status == 'free':
            reserv = models.GymReservations.objects.filter(type_id=type, date=day, time=slot).count()
            if reserv > 0:
                my = True
            if day > datetime.today() + timedelta(days=5):
                my = True

        if (status != 'free' or res < total_persons) and my == False:
            event_array = {}
            event_array['title'] = str(res) + "/" + str(total_persons)
            event_array['id'] = slot.id_slot
            if color is not None:
                event_array['color'] = color

            event_array['start'] = datetime.combine(day, slot.start_time).strftime("%Y-%m-%d %H:%M:%S")
            event_array['end'] = datetime.combine(day, slot.end_time).strftime("%Y-%m-%d %H:%M:%S")

            if status == 'free':
                event_array['extendedProps'] = {'isReserved': False}
            events_array.append(event_array)
    return events_array


def userReservToArray(resrvations, color=None):
    # print(resrvations)
    events_array = []
    for resrvation in resrvations:
        # print("ev ", resrvation)
        event_array = {}
        event_array['title'] = "Η κράτηση μου"
        event_array['id'] = resrvation.id_reservation
        if color is not None:
            event_array['color'] = color

        event_array['start'] = datetime.combine(resrvation.date, resrvation.time.start_time).strftime(
            "%Y-%m-%d %H:%M:%S")
        event_array['end'] = datetime.combine(resrvation.date, resrvation.time.end_time).strftime("%Y-%m-%d %H:%M:%S")

        event_array['extendedProps'] = {'isReserved': True}
        events_array.append(event_array)
    return events_array


def daysClosedList(days):
    # closed=[]
    # year=date.year
    # for day in days:
    #     d= datetime(year,day.month, day.day).strftime("%Y-%m-%d")
    #     closed.append(d)
    # return closed
    closed = []
    for day in days:
        closed.append(day.strftime("%Y-%m-%d"))
    return closed


@login_required()
@registration_completed()
def gymSlotsJSON(request):
    """

    :param request:
    :return:
    """
    eventsList = []
    print(request.POST)
    start = request.POST.get("start", None)
    end = request.POST.get("end", None)
    start = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None)
    end = datetime.strptime(end, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None)
    status = request.POST.get("status", None)
    type = request.POST.get("type", None)

    # closed= models.daysClosed.objects.filter(repeating = True).exclute(valid_to__lt) | models.daysClosed.objects.filter(date__gte=start.strftime("%Y-%m-%d"), date__lte= end.strftime("%Y-%m-%d"))
    # closed=daysClosedList(closed)
    closed = list(models.daysClosed.objects.filter(date__gte=start.strftime("%Y-%m-%d"),
                                                   date__lte=end.strftime("%Y-%m-%d")).values_list("date", flat=True))
    closed = daysClosedList(closed)
    slotsList = []
    if status == "free":
        if datetime.date(start) < datetime.date(datetime.today()):
            start = datetime.today()
        day = start
        while day.strftime("%Y-%m-%d") < end.strftime("%Y-%m-%d"):
            if day.strftime("%Y-%m-%d") not in closed and models.repeatingDaysClosed.objects.filter(
                    month=day.strftime("%m"), day=day.strftime("%d"),
                    valid_from__lte=day.strftime("%Y-%m-%d"), ).exclude(
                    valid_to__lt=day.strftime("%Y-%m-%d")).count() == 0:
                # print(date.today())
                if day.strftime("%Y-%m-%d") == datetime.today().strftime("%Y-%m-%d"):
                    slots = models.Slots.objects.filter(day=day.isoweekday(), type_id=int(type),
                                                        start_time__gte=datetime.today().strftime("%H:%M:%S"),
                                                        valid_from__lte=day.strftime("%Y-%m-%d")).exclude(
                        valid_to__lt=day.strftime("%Y-%m-%d"))
                else:
                    slots = models.Slots.objects.filter(day=day.isoweekday(), type_id=int(type),
                                                        valid_from__lte=day.strftime("%Y-%m-%d")).exclude(
                        valid_to__lt=day.strftime("%Y-%m-%d"))
                slotsList = slotsList + slotsToArray(type, day, slots, status)
            day = day + timedelta(days=1)
    elif status == "admin":
        day = start
        while day.strftime("%Y-%m-%d") < end.strftime("%Y-%m-%d"):
            if day.strftime("%Y-%m-%d") not in closed and models.repeatingDaysClosed.objects.filter(
                    month=day.strftime("%m"), day=day.strftime("%d"),
                    valid_from__lte=day.strftime("%Y-%m-%d"), ).exclude(
                    valid_to__lt=day.strftime("%Y-%m-%d")).count() == 0:
                slots = models.Slots.objects.filter(day=day.isoweekday(), type_id=type,
                                                    valid_from__lte=day.strftime("%Y-%m-%d")).exclude(
                    valid_to__lte=day.strftime("%Y-%m-%d"))
                slotsList = slotsList + slotsToArray(type, day, slots, status)
            day = day + timedelta(days=1)
    elif status == "user":
        resrvations = models.GymReservations.objects.filter(type_id=type, date__gte=start, date__lte=end,
                                                            user__user__username=request.user)
        slotsList = userReservToArray(resrvations)
    return JsonResponse(slotsList, safe=False)


@login_required()
@registration_completed()
def userGymCalendar(request, pk):
    try:
        type = models.Type.objects.get(pk=pk)

        if pk and type.active == True:
            context = {
                'type': type,
                'tab': 'gym'
            }
            return render(request, 'msfitcaregym/userGymCalendar.html', context)
        else:
            raise Http404("Calendar does not exist")
            # return HttpResponseNotFound('<h1>Page not found</h1>')
    except:
        raise Http404("Calendar does not exist")


@login_required()
@allowed_users(['admin'])
def adminGymCalendar(request, pk):
    try:
        type = models.Type.objects.get(pk=pk)
        if pk:
            users = models.UserProfile.objects.filter(accountStatus__in=['Accepted', 'NoUser'])
            # print("users: ", users)
            context = {
                "users": users,
                'type': type
            }
            return render(request, 'msfitcaregym/adminGymCalendar.html', context)
    except:
        raise Http404("Calendar does not exist")


@login_required()
@registration_completed()
def gymUserAddReservation(request):
    id = request.POST.get("id", None)
    type = request.POST.get("type", None)
    date = request.POST.get("date", None)
    userProfile = models.UserProfile.objects.get(user=request.user)
    print(request.POST)
    if models.GymReservations.objects.filter(date=date, user=userProfile, type_id=type).count() < 1:
        reservation = models.GymReservations(date=date, user=userProfile, type_id=type, time_id=id)
        reservation.save()
        data = {'msg': False}
    else:
        data = {'msg': True}

    return JsonResponse(data)


@login_required()
@allowed_users(['admin'])
def gymAdminReservations(request):
    id = request.POST.get("id", None)
    type = request.POST.get("type", None)
    date = request.POST.get("date", None)
    print(request.POST)
    # users=list(models.GymReservations.objects.filter(date=date,type_id=type, time_id=id).values_list("user",flat=True))
    users = models.GymReservations.objects.filter(date=date, type_id=type, time_id=id)
    # json = serializers.serialize('json', users)
    # return HttpResponse(json, content_type='application/json')
    data = []
    for user in users:
        name = user.user.first_name + " " + user.user.last_name
        d = {
            "name": name,
            "button": "<input type='button' value='Διαγραφή' onclick='removeReservation(\"" + name + "\"," + str(
                user.id_reservation) + ")'>",
            # "pk": user.id_reservation
        }
        data.append(d)
    # print(data)

    data = JsonResponse(data, safe=False)
    # print(data)
    return data


@login_required()
@allowed_users(['admin'])
def gymAdminAddReservation(request):
    print(request.POST)
    id = request.POST.get("id", None)
    type = request.POST.get("type", None)
    date = request.POST.get("date", None)
    user = request.POST.get("user", None)
    userProfile = models.UserProfile.objects.get(id=user)
    print(request.POST)

    reservation = models.GymReservations(date=date, user=userProfile, type_id=type, time_id=id)
    reservation.save()
    data = {'msg': "Reservation Added"}

    return JsonResponse(data)


@login_required()
@allowed_users(['admin'])
def gymAdminRemoveReservation(request):
    id = request.POST.get("id", None)

    models.GymReservations.objects.get(id_reservation=id).delete()

    data = {}
    return JsonResponse(data)


@login_required()
@registration_completed()
def gymUserRemoveReservation(request):
    id = request.POST.get("id", None)
    userProfile = models.UserProfile.objects.get(user=request.user)

    slot = models.GymReservations.objects.get(id_reservation=id, user=userProfile).delete()

    data = {}
    return JsonResponse(data)


@login_required()
@allowed_users(['admin'])
def daysClosed(request):
    daysClosed = models.daysClosed.objects.filter(date__gte=date.today())
    repeatingDaysClosed = models.repeatingDaysClosed.objects.all().exclude(valid_to__lt=date.today())
    # print(daysClosed)
    # print(repeatingDaysClosed)
    context = {
        "daysClosed": daysClosed,
        "repeatingDaysClosed": repeatingDaysClosed
    }
    return render(request, 'msfitcaregym/daysClosed.html', context)


@login_required()
@allowed_users(['admin'])
def addDayClosed(request):
    if request.POST:
        # print("post")
        date = request.POST.get("date", None)
        date = datetime.strptime(date, '%Y-%m-%d')
        repeating = request.POST.get('isRepeating', None)
        if repeating:

            newDate = models.repeatingDaysClosed(month=date.month, day=date.day, valid_from=date.today())
            newDate.save()
        else:
            newDate = models.daysClosed(date=date)
            newDate.save()
    return HttpResponseRedirect(reverse('msfitcaregym:daysClosed'))


@login_required()
@allowed_users(['admin'])
def removeDayClosed(request, repeating, pk):
    if repeating == 1:
        day = models.repeatingDaysClosed.objects.get(pk=pk)
        day.valid_to = date.today()
        day.save()
    else:
        models.daysClosed.objects.get(pk=pk).delete()
    return HttpResponseRedirect(reverse('msfitcaregym:daysClosed'))


def get_random_password_string(length):
    password_characters = string.ascii_letters + string.digits + "!@#%^&*()"
    password = ''.join(random.choice(password_characters) for i in range(length))
    return password

@login_required()
@allowed_users(['admin'])
def adminReservations(request,pk):
    user=models.UserProfile.objects.get(pk=pk)
    types=models.Type.objects.all()
    context = {
        "people": user,
        "types": types
    }
    return render(request, 'msfitcaregym/userReservations.html', context)

@login_required()
@registration_completed()
def userReservations(request):
    user=models.UserProfile.objects.get(user__username=request.user)
    types=models.Type.objects.all()
    context = {
        "people": user,
        "types": types
    }
    return render(request, 'msfitcaregym/userReservations.html', context)

@login_required()
def showReservations(request):
    pk = request.POST.get("pk", None)
    type = request.POST.get("type", None)
    print(request.POST)
    # users=list(models.GymReservations.objects.filter(date=date,type_id=type, time_id=id).values_list("user",flat=True))
    reservationsPhysio=[]
    reservationsGym=[]
    if type=="all":
        reservationsPhysio=models.PhysioReservations.objects.filter(user_id=pk)
        reservationsGym=models.GymReservations.objects.filter(user_id=pk)
    elif type=='physio':
        reservationsPhysio = models.PhysioReservations.objects.filter(user_id=pk)
    else:
        reservationsGym = models.GymReservations.objects.filter(user_id=pk,type_id=type)

    data = []
    for reservation in reservationsGym:
        d = {
            "type": reservation.type.Title,
            "date": reservation.date,
            'start':reservation.time.start_time,
            'end':reservation.time.end_time
        }
        data.append(d)
    # print(data)
    for reservation in reservationsPhysio:
        d = {
            "type": 'Φυσιοθεραπευτήριο',
            "date": reservation.date,
            'start':reservation.start_time,
            'end':reservation.end_time
        }
        data.append(d)
    # print(data)

    data = JsonResponse(data, safe=False)
    # print(data)
    return data


@login_required()
@allowed_users(['admin'])
def adminRegistrationForm(request):
    registration_form = forms.adminRegistrationForm(request.POST or None)
    if request.method == 'POST':
        print(request.POST)
        createUser = request.POST.get('createUser', None)
        if registration_form.is_valid():
            rform = registration_form.save(commit=False)
            if createUser is not None:
                user = models.User(first_name=rform.first_name, last_name=rform.last_name,
                                   email=request.POST.get('email'), username=request.POST.get('email'), is_active=True)
                password = get_random_password_string(10)
                # print(password)
                user.set_password(password)
                user.save()
                rform.user = user
                rform.accountStatus = 'Accepted'

                subject = 'MSFitCareGym Λογαριασμός'
                message = f'{rform.first_name} καλωσόρισες, το MSFitCareGym σας έχει δημιουργήσει λογαριασμό στo msfitcaregym.com' \
                          f'Μπορείτε να εισέλθετε στο λογαριασμό σας με το email {user.username} και τον κωδικό {password}'
                email_from = settings.EMAIL_HOST_USER
                recipient_list = [user.username, ]
                send_mail(subject, message, email_from, recipient_list)
            else:
                rform.accountStatus = 'NoUser'
            rform.save()
            return redirect('msfitcaregym:usersinfo')
        else:
            print(registration_form.errors)
            messages.info(request, 'Το προφίλ για τον συγκεκριμένο χρήστη έχει ήδη καταχωρηθεί')

    context = {
        'registration_form': registration_form,
        'tab': 'registration_form'
    }
    return render(request, 'msfitcaregym/adminRegistrationform.html', context)


@login_required()
def Logout(request):
    logout(request)
    return redirect('msfitcaregym:login')


@login_required()
def RegistrationForm(request):
    user = request.user
    if request.method == 'POST':
        userp = get_object_or_404(models.UserProfile, user=user)
        registration_form = forms.RegistrationForm(data=request.POST, instance=userp)
        if registration_form.is_valid():
            rform = registration_form.save(commit=False)
            rform.user = user
            rform.save()
            return redirect('msfitcaregym:dashboard')
        else:
            print(registration_form.errors)
            messages.info(request, 'Το προφίλ για τον συγκεκριμένο χρήστη έχει ήδη καταχωρηθεί')
    else:
        userp = get_object_or_404(models.UserProfile, user=user)
        registration_form = forms.RegistrationForm(instance=userp,initial={'user': user})
    context = {
        'registration_form': registration_form,
        'tab': 'registration_form'
    }
    return render(request, 'msfitcaregym/registrationform.html', context)


def WorkingHours(request):
    hours = models.WorkingHours.objects.all()
    context = {
        'hours':hours,
        'tab': 'working_hours'
    }
    return render(request, 'msfitcaregym/working_hours.html', context)


def Pricing(request):
    packages = models.Packages.objects.all().order_by('price')
    physio = models.PhysioPrices.objects.all().order_by('price')
    packageform = forms.PackageForm(request.POST or None)
    physioform = forms.PhysioPricesForm(request.POST or None)
    if request.method == 'POST':
        if request.POST.get("save_price"):
            if packageform.is_valid():
                pform = packageform.save()
            return HttpResponseRedirect(reverse('msfitcaregym:pricing'))
        elif request.POST.get("save_physio"):
            if physioform.is_valid():
                physioform1 = physioform.save()
            return HttpResponseRedirect(reverse('msfitcaregym:pricing'))

    context = {
        'packages': packages,
        'physio': physio,
        'tab': 'pricing',
        'form': packageform,
        'pform': physioform
    }
    return render(request, 'msfitcaregym/pricing.html', context)


@login_required()
@allowed_users(['admin'])
def remove_pricing(request, pk=None):
    """
    :param request:
    :param pk:
    :param acc:
    :return:
    """
    if pk:
        models.Packages.objects.filter(pk=pk).delete()
        return HttpResponseRedirect(reverse('msfitcaregym:pricing'))


@login_required()
@allowed_users(['admin'])
def remove_pricing_physio(request, pk=None):
    """
    :param request:
    :param pk:
    :param acc:
    :return:
    """
    if pk:
        models.PhysioPrices.objects.filter(pk=pk).delete()
        return HttpResponseRedirect(reverse('msfitcaregym:pricing'))


@login_required()
@registration_completed()
def Profile(request):
    user = request.user
    userform = forms.UserForm(request.POST or None, instance=user)
    userprofile = models.UserProfile.objects.get(user=user)
    userprofileform = forms.ProfileForm(request.POST or None, instance=userprofile)
    if request.method == 'POST':
        if userform.is_valid() and userprofileform.is_valid():
            uform = userform.save(commit=True)
            pform = userprofileform.save(commit=False)
            pform.user = uform
            pform.save()
        else:
            print(userform.errors, userprofileform.errors)
            messages.info(request, userform.errors + userprofileform.errors)
    else:
        user = request.user
        userform = forms.UserForm(instance=user)
        userprofile = models.UserProfile.objects.get(user=user)
        userprofileform = forms.ProfileForm(instance=userprofile)
    context = {
        'user_form': userform,
        'profile_form': userprofileform
    }
    return render(request, 'msfitcaregym/profile.html', context)


@login_required()
@allowed_users(['admin'])
def HumanBody1(request, pk=None):
    if pk:
        context = {
            'card_id': pk
        }
    return render(request, 'msfitcaregym/humanbody1.html', context)


# def HumanBody(request,pk=None):
#     if pk:
#         context = {
#             'card_id':pk
#         }
#         return render(request,'msfitcaregym/humanbody.html',context)

# def DisplayHumanBody(request,pk=None):
#     if pk:
#         card = models.PhysioCard.objects.get(pk=pk)
#         bodyparts = models.BodyParts.objects.filter(physio_card_id = pk)
#         context = {
#             'card_id':pk,
#             'card':card,
#             'bodyparts':bodyparts,
#             'display':1,
#         }
#         return render(request,'msfitcaregym/displayhumanbody.html',context)

@login_required()
@allowed_users(['admin'])
def DisplayHumanBody1(request, pk=None):
    if pk:
        card = models.PhysioCard.objects.get(pk=pk)
        bodyparts = models.BodyParts.objects.filter(physio_card_id=pk)
        # print(bodyparts)
        context = {
            'card_id': pk,
            'card': card,
            'bodyparts': bodyparts,
            'display': 1,
        }
        return render(request, 'msfitcaregym/displayhumanbody1.html', context)


def Galery(request):
    gallery = models.Gallery.objects.all()
    galleryform = forms.GalleryForm(request.POST or None)

    if request.method == 'POST':
        print(request.POST)
        id_type = request.POST.get('type_id', None)
        if id_type:
            type = models.Type.objects.get(id_type=id_type)
            type.total_persons = request.POST.get('max_res', None)
            type.save()
        else:
            if galleryform.is_valid():
                form = galleryform.save()
                if 'photo' in request.FILES:
                    form.photo = request.FILES['photo']

                if request.POST.get('addReservation'):
                    type = models.Type(Title=request.POST.get('title', None),
                                       total_persons=request.POST.get('max_res', None), active=True)
                    type.save()
                    form.reservation = type
                form.save()
            return HttpResponseRedirect(reverse('msfitcaregym:galery'))
    context = {
        'tab': 'galery',
        'gallery': gallery,
        'form': galleryform,
    }
    return render(request, 'msfitcaregym/galery.html', context)


@login_required()
@allowed_users(['admin'])
def remove_gallery(request, pk=None):
    """
    :param request:
    :param pk:
    :param acc:
    :return:
    """
    if pk:
        g = models.Gallery.objects.get(pk=pk)
        if g.reservation:
            g.reservation.active = False
            g.reservation.save()
        g.delete()
        return HttpResponseRedirect(reverse('msfitcaregym:galery'))


def AboutUs(request):
    about = models.AboutUs.objects.all()
    aboutusform = forms.AboutUsForm(request.POST or None)

    if request.method == 'POST':
        if aboutusform.is_valid():
            form = aboutusform.save()
            if 'photo' in request.FILES:
                form.photo = request.FILES['photo']
            form.save()
            return HttpResponseRedirect(reverse('msfitcaregym:aboutus'))

    context = {
        'about': about,
        'tab': 'about_us',
        'form': aboutusform
    }
    return render(request, 'msfitcaregym/about-us.html', context)


@login_required()
@allowed_users(['admin'])
def remove_aboutus(request, pk=None):
    """
    :param request:
    :param pk:
    :param acc:
    :return:
    """
    if pk:
        models.AboutUs.objects.filter(pk=pk).delete()
        return HttpResponseRedirect(reverse('msfitcaregym:aboutus'))


@login_required()
@allowed_users(['admin'])
def remove_program(request, pk=None):
    """
    :param request:
    :param pk:
    :param acc:
    :return:
    """
    if pk:
        program = models.ProgramUser.objects.filter(pk=pk)
        programday = models.ProgramDates.objects.filter(program_id=pk)
        for d in programday:
            exercises = models.ExercisesPerDate.objects.filter(id_program_Date_id=d.pk)
            for e in exercises:
                e.delete()
            d.delete()
        program.delete()

        return HttpResponseRedirect(reverse('msfitcaregym:userprogramhistory'))


@login_required()
@allowed_users(['admin'])
def remove_program_day(request, pk=None):
    """
    :param request:
    :param pk:
    :param acc:
    :return:
    """
    if pk:
        programday = models.ProgramDates.objects.filter(pk=pk)
        program = models.ProgramUser.objects.filter(pk=programday[0].program_id)
        for d in programday:
            exercises = models.ExercisesPerDate.objects.filter(id_program_Date_id=d.pk)
            for e in exercises:
                e.delete()
            d.delete()
        url = '/userprogramperdayedit/' + str(program[0].pk) + '/'
        return HttpResponseRedirect(url)


@login_required()
def Announcements(request):
    announcements = models.Announcements.objects.all().order_by('-submited_date')
    ann_form = forms.AnnouncementsForm(request.POST or None)
    if request.method == 'POST':
        if ann_form.is_valid():
            ann = ann_form.save(commit=False)
            ann.submited_date = datetime.today()
            ann.save()
            return HttpResponseRedirect(reverse('msfitcaregym:announcements'))
    context = {
        'tab': 'announcements',
        'announcements': announcements,
        'tab': 'announcement',
        'form': ann_form

    }
    return render(request, 'msfitcaregym/announcement.html', context)


@login_required()
@allowed_users(['admin'])
def remove_announcement(request, pk=None):
    """
    :param request:
    :param pk:
    :param acc:
    :return:
    """
    if pk:
        models.Announcements.objects.filter(pk=pk).delete()
        return HttpResponseRedirect(reverse('msfitcaregym:announcements'))


@login_required()
@allowed_users(['admin'])
def UsersInfo(request):
    if request.method == "POST":
        print(request.POST)
        user = request.POST.get("user")
        email = request.POST.get("email")
        profile = models.UserProfile.objects.get(pk=user)
        user = models.User(first_name=profile.first_name, last_name=profile.last_name, email=email, username=email,
                           is_active=True)
        profile.user = user
        profile.accountStatus = "Accepted"
        password = get_random_password_string(10)
        # print(password)
        user.set_password(password)
        user.save()
        profile.save()
        subject = 'MSFitCareGym Λογαριασμός'
        message = f'{profile.first_name} καλωσόρισες, το MSFitCareGym σας έχει δημιουργήσει λογαριασμό στo msfitcaregym.com' \
                  f'Μπορείτε να εισέλθετε στο λογαριασμό σας με το email {user.username} και τον κωδικό {password}'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [user.username, ]
        send_mail(subject, message, email_from, recipient_list)
        return HttpResponseRedirect(reverse('msfitcaregym:usersinfo'))
    users = models.UserProfile.objects.filter(accountStatus__in=['Accepted', 'Rejected', 'Revoke'])
    # print(users)
    request_users = models.UserProfile.objects.filter(accountStatus='Request')
    # print(request_users)
    no_users = models.UserProfile.objects.filter(accountStatus='NoUser')
    context = {
        'users': users,
        'req': request_users,
        'no_users': no_users
    }
    return render(request, 'msfitcaregym/usersInfo.html', context)


@login_required()
@allowed_users(['admin'])
def userRequestApprovalChange(request, pk=None, acc=None):
    """
    :param request:
    :param pk:
    :param acc:
    :return:
    """
    if pk:
        userProfile = get_object_or_404(models.UserProfile, pk=pk)
        user = get_object_or_404(models.User, pk=userProfile.user.pk)
        # print(user)

        if acc == "True":
            userProfile.accountStatus = "Accepted"
            user.is_active = True
            subject = 'MSFitCareGym Λογαριασμός'
            message = f'{user.first_name} καλωσόρισες, το MSFitCareGym σας έχει ενεργοποίησει τον λογαριασμό σας' \
                      f'Μπορείτε να εισέλθετε στο λογαριασμό σας με το email {user.username}'
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [user.username, ]
            send_mail(subject, message, email_from, recipient_list)
        elif acc == "False":
            userProfile.accountStatus = "Rejected"
            user.is_active = False

        userProfile.save()
        user.save()
        return HttpResponseRedirect(reverse('msfitcaregym:usersinfo'))


@login_required()
@allowed_users(['admin'])
def UserProgram(request):
    programuserform = forms.ProgramUserForm(request.POST or None)
    if request.method == 'POST':
        if programuserform.is_valid():
            pform = programuserform.save(commit=True)
            request.session['user_pk'] = pform.pk
            return HttpResponseRedirect(reverse('msfitcaregym:programperday'))
        else:
            messages.error(request, 'Please fill the form')
    context = {
        'programuser': programuserform,
    }
    return render(request, 'msfitcaregym/programuser.html', context)


@login_required()
@allowed_users(['admin'])
def EditUserProgram(request):
    users = models.UserProfile.objects.filter(accountStatus__in=['Accepted', 'NoUser'])
    if request.method == 'POST':
        user = request.POST.get('users', '')
        request.session['edit_user_pk'] = user
        return HttpResponseRedirect(reverse('msfitcaregym:userprogramhistory'))

    context = {
        'users': users,
    }
    return render(request, 'msfitcaregym/programuseredit.html', context)


@login_required()
@registration_completed()
def UserProgramHistory(request):
    userProf = models.UserProfile.objects.get(pk=request.session.get('edit_user_pk'))
    try:
        programs = models.ProgramUser.objects.filter(user_id=userProf.pk).order_by('-date')
    except:
        programs = None

    context = {
        'programs': programs
    }
    return render(request, 'msfitcaregym/historyprogramuser.html', context)


@login_required()
@registration_completed()
def displayProgramHistory(request):
    userProf = models.UserProfile.objects.get(user=request.user)
    try:
        programs = models.ProgramUser.objects.filter(user_id=userProf.pk).order_by('-date')
    except:
        programs = None

    context = {
        'programs': programs
    }
    return render(request, 'msfitcaregym/historyprogramuser.html', context)


@login_required()
def UserProgramPerDayEdit1(request, pk=None):
    if pk:
        try:
            program = models.ProgramUser.objects.get(pk=pk)
            prof = models.UserProfile.objects.get(pk=program.user_id)
            program_days = models.ProgramDates.objects.filter(program=program).order_by('title')

            for p in program_days:
                exercises = models.ExercisesPerDate.objects.filter(id_program_Date=p.pk).values()
                for e in exercises:
                    e['id_exercises_id'] = models.Exercises.objects.get(pk=e['id_exercises_id'])
                p.exercises = exercises
        except:
            program = None
            program_days = None

        context = {
            'userp': prof,
            'program': program,
            'program_days': program_days
        }
        return render(request, 'msfitcaregym/displayprogramedit.html', context)


@login_required()
@allowed_users(['admin'])
def UserProgramPerDay(request):
    programuser = get_object_or_404(models.ProgramUser, pk=request.session.get('user_pk'))
    programday = forms.ProgramDayForm(request.POST or None, initial={'program': request.session.get('user_pk')})
    exercises = forms.ProgramFormset(request.POST or None)
    if request.method == 'POST':
        print(request.POST)
        if programday.is_valid():
            pday = programday.save(commit=False)
        if exercises.is_valid():
            pday.save()
            for form in exercises:
                if form.is_valid():
                    f = form.save(commit=False)
                    f.id_program_Date = pday
                    if f.color == 'FFFFFF':
                        f.color = '000000'
                    f.save()
                else:
                    messages.error(request, 'Η μέρα δεν έχει αποθηκευτεί')
            messages.success(request, 'Η μέρα έχει αποθηκευτεί με επιτυχία')
            return HttpResponseRedirect(reverse('msfitcaregym:programperday'))
        else:
            messages.error(request, 'Η μέρα δεν έχει αποθηκευτεί')
    context = {
        'programday': programday,
        'ex_form': exercises
    }
    return render(request, 'msfitcaregym/programperday.html', context)


@login_required()
@allowed_users(['admin'])
def UserProgramPerDayEdit(request):
    userProf = models.UserProfile.objects.get(pk=request.session.get('edit_user_pk'))
    try:
        program = models.ProgramUser.objects.filter(user_id=userProf.pk).latest('date')
        program_days = models.ProgramDates.objects.filter(program=program).order_by('title')
        # print(program_days)

        for p in program_days:
            exercises = models.ExercisesPerDate.objects.filter(id_program_Date=p.pk).values()
            for e in exercises:
                e['id_exercises_id'] = models.Exercises.objects.get(pk=e['id_exercises_id'])
            p.exercises = exercises
    except:
        program = None
        program_days = None

    context = {
        'user': userProf.user,
        'program': program,
        'program_days': program_days
    }
    return render(request, 'msfitcaregym/displayprogramedit.html', context)


@login_required()
@registration_completed()
def displayUserProgram(request):
    user = request.user
    try:
        userProf = models.UserProfile.objects.get(user=user)
        program = models.ProgramUser.objects.filter(user_id=userProf.pk).latest('date')
        program_days = models.ProgramDates.objects.filter(program=program).order_by('title')

        for p in program_days:
            exercises = models.ExercisesPerDate.objects.filter(id_program_Date=p.pk).values()
            for e in exercises:
                e['id_exercises_id'] = models.Exercises.objects.get(pk=e['id_exercises_id'])
            p.exercises = exercises
    except:
        program = None
        program_days = None

    context = {
        'user': user,
        'program': program,
        'program_days': program_days,
        'tab': 'myprogram'
    }

    return render(request, 'msfitcaregym/displayUserProgram.html', context)


@login_required()
@allowed_users(['admin'])
def EditDay(request, pk=None):
    if pk:
        program_day = models.ProgramDates.objects.get(pk=pk)
        program = models.ProgramUser.objects.filter(pk=program_day.program_id)
        url = '/userprogramperdayedit/' + str(program[0].pk) + '/'
        programday = forms.ProgramDayForm(request.POST or None, instance=program_day)
        exercisesall = models.ExercisesPerDate.objects.filter(id_program_Date=program_day.pk)
        exercises = forms.ProgramFormsetEdit(request.POST or None, queryset=exercisesall)
        if request.method == 'POST':
            print(request.POST)
            if programday.is_valid():
                pday = programday.save(commit=True)
            if exercises.is_valid():
                for form in exercises:
                    if form.is_valid():
                        f = form.save(commit=False)
                        f.id_program_Date = pday
                        if f.color == 'FFFFFF':
                            f.color = '000000'
                        f.save()
                    else:
                        messages.error(request, 'Η μέρα δεν έχει αποθηκευτεί')
                return HttpResponseRedirect(url)
            else:
                messages.error(request, 'Η μέρα δεν έχει αποθηκευτεί')
        context = {
            'programday': programday,
            'ex_form': exercises
        }
        return render(request, 'msfitcaregym/programperdayedit.html', context)


@login_required()
@registration_completed()
def displayDay(request, pk=None):
    if pk:
        try:
            program_day = models.ProgramDates.objects.get(pk=pk)
            exercisesall = models.ExercisesPerDate.objects.filter(id_program_Date=program_day.pk)
        except:
            program_day = None
            exercisesall = None

        context = {
            'program_day': program_day,
            'exercises': exercisesall
        }
        return render(request, 'msfitcaregym/displayDay.html', context)


@login_required()
@allowed_users(['admin'])
def Payments(request):
    form = forms.PaymentsForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save(commit=True)
        else:
            messages.error(request, "Η καταχώρηση πληρωμής δεν έχει γίνει")
        messages.success(request, "Η πληρωμή έχει καταχωρηθεί με επιτυχία")
        return redirect('msfitcaregym:addpayments')
    context = {
        'form': form
    }
    return render(request, 'msfitcaregym/payments.html', context)


@login_required()
@registration_completed()
def allPayments(request):
    users = models.UserProfile.objects.all()
    for u in users:
        try:
            u.payment = models.Payments.objects.filter(user=u).latest('pay_until')
            today = datetime.now()
            day = datetime.strptime(u.payment.pay_until.strftime('%Y%m%d'), '%Y%m%d')
            daysdifference = (today - day).days
            if daysdifference > 0:
                u.over = True
            else:
                u.over = False
        except:
            u.payment = None
    context = {
        'users': users
    }
    return render(request, 'msfitcaregym/allPayments.html', context)


@login_required()
@allowed_users(['admin'])
def editPayments(request, pk=None):
    if pk:
        userpayment = models.Payments.objects.get(id_payment=pk)
        paymentform = forms.PaymentsForm(request.POST or None, instance=userpayment)
        if request.method == 'POST':
            if paymentform.is_valid():
                paymentform.save(commit=True)
            else:
                messages.error(request, "Η επεξεργασία της πληρωμής δεν έχει καταχωρηθεί")
            return redirect('msfitcaregym:allpayments')
        context = {
            'userpayment': userpayment,
            'form': paymentform
        }
        return render(request, 'msfitcaregym/editPayment.html', context=context)


@login_required()
@allowed_users(['admin'])
def userPayments(request, pk=None):
    if pk:
        try:
            userprof = models.UserProfile.objects.get(pk=pk)
            payments = models.Payments.objects.filter(user=userprof).order_by('-pay_until')
            today = datetime.today().date()
            for p in payments:
                if today > p.pay_until:
                    p.over = True
                else:
                    p.over = False
        except:
            payments = None

        context = {
            'payments': payments,
            'userprof': userprof,
        }
        return render(request, 'msfitcaregym/userpayments.html', context)


@login_required()
@registration_completed()
def paymentsUser(request):
    try:
        user = request.user
        userprof = models.UserProfile.objects.get(user=user)
        payments = models.Payments.objects.filter(user=userprof).order_by('-pay_until')
        payment = models.Payments.objects.filter(user=userprof).latest('pay_until')
        today = datetime.today().date()
        for p in payments:
            if today > p.pay_until:
                p.over = True
            else:
                p.over = False
    except:
        payments = None
        payment = None
        userprof = models.UserProfile.objects.get(user=user)

    context = {
        'payments': payments,
        'userprof': userprof,
        'payment': payment
    }
    return render(request, 'msfitcaregym/userpayments.html', context)


@login_required()
@allowed_users(['admin'])
def BlockUser(request, pk=None, acc=None):
    """
    :param request:
    :param pk:
    :param acc:
    :return:
    """
    if pk:
        userProfile = get_object_or_404(models.UserProfile, pk=pk)
        user = get_object_or_404(models.User, pk=userProfile.user.pk)

        if acc == "True":
            userProfile.accountStatus = "Accepted"
            user.is_active = True
        elif acc == "False":
            userProfile.accountStatus = "Revoke"
            user.is_active = False

        userProfile.save()
        user.save()
        return HttpResponseRedirect(reverse('msfitcaregym:allpayments'))


@login_required()
@allowed_users(['admin'])
def BlockUserInfo(request, pk=None, acc=None):
    """
    :param request:
    :param pk:
    :param acc:
    :return:
    """
    if pk:
        userProfile = get_object_or_404(models.UserProfile, pk=pk)
        user = get_object_or_404(models.User, pk=userProfile.user.pk)

        if acc == "True":
            userProfile.accountStatus = "Accepted"
            user.is_active = True
        elif acc == "False":
            userProfile.accountStatus = "Revoke"
            user.is_active = False

        userProfile.save()
        user.save()
        return HttpResponseRedirect(reverse('msfitcaregym:usersinfo'))


@login_required()
@registration_completed()
def checkAnnouncements(request):
    user = request.user
    try:
        profile = models.UserProfile.objects.get(user=user)
        profile.checkann = datetime.today()
        profile.save()
    except:
        profile = None
    data = {}
    return JsonResponse(data)


@login_required()
@allowed_users(['admin'])
def saveModal(request):
    print(request.POST)
    part = request.POST['part']
    card_id = request.POST['card']
    try:
        body = models.BodyParts.objects.get(physio_card_id=card_id, part_position=part)
    except:
        body = None
    if body is not None:
        form = forms.BodyPartForm(instance=body)
        f = form.save(commit=False)
        f.details = request.POST['details']
        f.save()
    else:
        form = forms.BodyPartForm()
        f = form.save(commit=False)
        f.physio_card_id = request.POST['card']
        f.part_position = request.POST['part']
        f.details = request.POST['details']
        f.save()
    data = {'details': f.details, 'id': f.part_position}
    return JsonResponse(data)


@login_required()
@allowed_users(['admin'])
def saveModaltest(request):
    print(request.POST)
    comments = request.POST['comments']
    card_id = request.POST['card']
    x = request.POST['x']
    y = request.POST['y']
    circle_id = request.POST['circle_id']
    color = request.POST['color']
    # print(color)
    try:
        body = models.BodyParts.objects.get(physio_card_id=card_id, circle_id=circle_id, x=x, y=y)
    except:
        body = None
    if body is not None:
        form = forms.BodyPartForm(instance=body)
        f = form.save(commit=False)
        f.physio_card_id = card_id
        f.circle_id = circle_id
        f.details = comments
        f.x = x
        f.y = y
        f.color = color
        f.save()
    else:
        form = forms.BodyPartForm()
        f = form.save(commit=False)
        f.physio_card_id = card_id
        f.circle_id = circle_id
        f.details = comments
        f.x = x
        f.y = y
        f.color = color
        f.save()
    data = {'details': f.details, 'id': f.circle_id, 'x': f.x, 'y': f.y, 'color': f.color}
    return JsonResponse(data)


@login_required()
@allowed_users(['admin'])
def removeBodyPart(request):
    print(request.POST)
    comments = request.POST['comments']
    card_id = request.POST['card']
    x = request.POST['x']
    y = request.POST['y']
    circle_id = request.POST['circle_id']
    color = request.POST['color']
    # print(color)
    try:
        body = models.BodyParts.objects.get(physio_card_id=card_id, circle_id=circle_id, x=x, y=y, details=comments)
        body.delete()
    except:
        body = None
    data = {'details': comments, 'id': circle_id, 'x': x, 'y': y, 'color': color}
    return JsonResponse(data)


@login_required()
@allowed_users(['admin'])
def addCommentsCard(request):
    card_id = request.POST['card_id']
    comments = request.POST['comments']
    card = models.PhysioCard.objects.get(pk=card_id)
    card.comments = comments
    card.save()
    data = {'comments': comments}
    return JsonResponse(data)


@login_required()
@allowed_users(['admin'])
def addExtraDay(request):
    pk = request.POST['program_id']
    request.session['user_pk'] = pk
    data = {}
    return JsonResponse(data)


def displayRegistrationForm(request, pk=None):
    if pk:
        try:
            userprofile = models.UserProfile.objects.get(pk=pk)
            form = forms.adminRegistrationForm(request.POST or None ,instance=userprofile)
        except:
            userprofile = None
            form = None

        if request.method == 'POST':
            if form.is_valid():
                rform = form.save(commit=False)
                if userprofile.user:
                    email = request.POST.get('email')
                    user = models.User.objects.get(pk = userprofile.user_id)
                    user.username = email
                    user.save()
                    rform.save()
                else:
                    rform.save()
                return HttpResponseRedirect(reverse('msfitcaregym:usersinfo'))

        context = {
            'profile': userprofile,
            'registration_form' : form,
        }
        return render(request, 'msfitcaregym/displayregistrationform.html', context)

def saveHours(request):
    id_day = request.POST['id_day']
    day = request.POST['day']
    time = request.POST['time']
    w_day = models.WorkingHours.objects.get(pk = id_day)
    w_day.day = day
    w_day.time = time
    w_day.save()
    data = {}
    return JsonResponse(data)

@login_required()
@allowed_users(['admin'])
def allExercises(request):
    form = forms.ExerciseForm(request.POST or None)
    exercises = models.Exercises.objects.all()

    if request.method == 'POST':
        if form.is_valid():
            form = form.save()
            return HttpResponseRedirect(reverse('msfitcaregym:allexercises'))
    context = {
        'exercises': exercises,
        'form':form,
    }
    return render(request, 'msfitcaregym/allexercises.html', context)

@login_required()
@allowed_users(['admin'])
def remove_exercise(request, pk=None):
    """
    :param request:
    :param pk:
    :param acc:
    :return:
    """
    if pk:
        models.Exercises.objects.filter(pk=pk).delete()
        return HttpResponseRedirect(reverse('msfitcaregym:allexercises'))


def addhours():
    models.WorkingHours.objects.update_or_create(day= "Κυριακή", time= "Κλειστό" )
    models.WorkingHours.objects.update_or_create(day= "Δευτέρα", time= "6:00 - 21:30" )
    models.WorkingHours.objects.update_or_create(day= "Τρίτη", time= "6:00 - 21:30" )
    models.WorkingHours.objects.update_or_create(day= "Τετάρτη", time= "6:00 - 21:30" )
    models.WorkingHours.objects.update_or_create(day= "Πέμπτη", time= "6:00 - 21:30" )
    models.WorkingHours.objects.update_or_create(day= "Παρασκευή", time= "6:00 - 21:00" )
    models.WorkingHours.objects.update_or_create(day= "Σάββατο", time= "7:00 - 17:00" )

def addCategories():
    models.Categories.objects.update_or_create(name="Πόδια")
    models.Categories.objects.update_or_create(name="'Ωμοι")
    models.Categories.objects.update_or_create(name="Στήθος")
    models.Categories.objects.update_or_create(name="Πλάτη")
    models.Categories.objects.update_or_create(name="Τρικέφαλο")
    models.Categories.objects.update_or_create(name="Δικέφαλο")
    models.Categories.objects.update_or_create(name="Κοιλιακοί")
    models.Categories.objects.update_or_create(name="Ραχιαίοι")
    models.Categories.objects.update_or_create(name="CV Αερόβιο")


def addExercises():
    models.Exercises.objects.update_or_create(name="Leg Press",category_id=1)
    models.Exercises.objects.update_or_create(name="Leg Press(Open)",category_id=1)
    models.Exercises.objects.update_or_create(name="Leg Press(Μπάλα)", category_id=1)
    models.Exercises.objects.update_or_create(name="Leg Extension", category_id=1)
    models.Exercises.objects.update_or_create(name="Leg Curl", category_id=1)
    models.Exercises.objects.update_or_create(name="Adductor",category_id=1)
    models.Exercises.objects.update_or_create(name="Abductor",category_id=1)
    models.Exercises.objects.update_or_create(name="Rear Kick",category_id=1)
    models.Exercises.objects.update_or_create(name="Calf",category_id=1)
    models.Exercises.objects.update_or_create(name="Squats(smith)",category_id=1)
    models.Exercises.objects.update_or_create(name="Squats(H.R)",category_id=1)
    models.Exercises.objects.update_or_create(name="Wall Squats",category_id=1)
    models.Exercises.objects.update_or_create(name="Front Squats",category_id=1)
    models.Exercises.objects.update_or_create(name="Lunges(Αλτήρες)",category_id=1)
    models.Exercises.objects.update_or_create(name="Walking Lunges",category_id=1)
    models.Exercises.objects.update_or_create(name="Lunges(smith)",category_id=1)
    models.Exercises.objects.update_or_create(name="Sumo Squats(Αλτήρα)",category_id=1)
    models.Exercises.objects.update_or_create(name="Sumo Squats(H.R)",category_id=1)
    models.Exercises.objects.update_or_create(name="Romanian didlift",category_id=1)
    models.Exercises.objects.update_or_create(name="Γλουτούς(τροχαλία)",category_id=1)
    models.Exercises.objects.update_or_create(name="Shuffle(Λάστιχο)",category_id=1)
    models.Exercises.objects.update_or_create(name="Bringes(Bosu)",category_id=1)
    models.Exercises.objects.update_or_create(name="Bringes(Bar)",category_id=1)
    models.Exercises.objects.update_or_create(name="Bringes(L.E)",category_id=1)
    models.Exercises.objects.update_or_create(name="Multi Hip(τετρακέφαλο)",category_id=1)
    models.Exercises.objects.update_or_create(name="Multi Hip(δικέφαλο Μηριαίο)",category_id=1)
    models.Exercises.objects.update_or_create(name="Multi Hip(προσαγωγούς)",category_id=1)
    models.Exercises.objects.update_or_create(name="Multi Hip(Απαγωγοί)",category_id=1)
    models.Exercises.objects.update_or_create(name="Multi Hip(Γλουτούς)",category_id=1)
    models.Exercises.objects.update_or_create(name="Calves(L.P)",category_id=1)
    models.Exercises.objects.update_or_create(name="Calves(smith)",category_id=1)
    models.Exercises.objects.update_or_create(name="Shoulder Press",category_id=2)
    models.Exercises.objects.update_or_create(name="Shoulder Press(Μπροστά)", category_id=2)
    models.Exercises.objects.update_or_create(name="Pelts Machine",category_id=2)
    models.Exercises.objects.update_or_create(name="Front Raise",category_id=2)
    models.Exercises.objects.update_or_create(name="Lateral Raise",category_id=2)
    models.Exercises.objects.update_or_create(name="Scaption",category_id=2)
    models.Exercises.objects.update_or_create(name="Military Press",category_id=2)
    models.Exercises.objects.update_or_create(name="Πιέσεις ώμων(αλτήρες)",category_id=2)
    models.Exercises.objects.update_or_create(name="Arnold Press",category_id=2)
    models.Exercises.objects.update_or_create(name="Front Raise(Bar)",category_id=2)
    models.Exercises.objects.update_or_create(name="Lateral Raise(τροχαλία)",category_id=2)
    models.Exercises.objects.update_or_create(name="Upright Row(τροχαλία)",category_id=2)
    models.Exercises.objects.update_or_create(name="Upright Row(Bar)",category_id=2)
    models.Exercises.objects.update_or_create(name="Εκτάσεις πλάι σκυφτός",category_id=2)
    models.Exercises.objects.update_or_create(name="Χιαστή στη τροχαλία",category_id=2)
    models.Exercises.objects.update_or_create(name="Τραπεζοειδής(Αλτήρες)",category_id=2)
    models.Exercises.objects.update_or_create(name="Τραπεζοειδής (smith)",category_id=2)
    models.Exercises.objects.update_or_create(name="Shoulder Compo",category_id=2)
    models.Exercises.objects.update_or_create(name="Chest Press",category_id =3)
    models.Exercises.objects.update_or_create(name="Chest Press(smith)",category_id=3)
    models.Exercises.objects.update_or_create(name="Chest Press(dumbbell)",category_id=3)
    models.Exercises.objects.update_or_create(name="Chest Press(dumbbell-15°)",category_id=3)
    models.Exercises.objects.update_or_create(name="Inline Press(smith)",category_id=3)
    models.Exercises.objects.update_or_create(name="Inline Press(dumbbell)",category_id=3)
    models.Exercises.objects.update_or_create(name="Inline Press(H.R)",category_id=3)
    models.Exercises.objects.update_or_create(name="Flyes (dumbbell)",category_id=3)
    models.Exercises.objects.update_or_create(name="Flyes(dumbbell-15°)",category_id=3)
    models.Exercises.objects.update_or_create(name="Wide Chest Press",category_id=3)
    models.Exercises.objects.update_or_create(name="Pecu Decu",category_id=3)
    models.Exercises.objects.update_or_create(name="Pectoral",category_id=3)
    models.Exercises.objects.update_or_create(name="Cross Over",category_id=3)
    models.Exercises.objects.update_or_create(name="Low cable cross over",category_id=3)
    models.Exercises.objects.update_or_create(name="Flyes cable(Bench-15°)",category_id=3)
    models.Exercises.objects.update_or_create(name="Close chest(dumbbell-15°)",category_id=3)
    models.Exercises.objects.update_or_create(name="Pull Over",category_id=3)
    models.Exercises.objects.update_or_create(name="Push Up",category_id=3)
    models.Exercises.objects.update_or_create(name="Dincline Press(dumbbell)",category_id=3)
    models.Exercises.objects.update_or_create(name="Dincline Press(smith)",category_id=3)
    models.Exercises.objects.update_or_create(name="Push Up(Bosu)",category_id=3)
    models.Exercises.objects.update_or_create(name="Lat Machine(open)",category_id=4)
    models.Exercises.objects.update_or_create(name="Lat Machine(close)",category_id=4)
    models.Exercises.objects.update_or_create(name="Pull Down",category_id=4)
    models.Exercises.objects.update_or_create(name="Pulley",category_id=4)
    models.Exercises.objects.update_or_create(name="Pulley(open)",category_id=4)
    models.Exercises.objects.update_or_create(name="Pulley(Rope)",category_id=4)
    models.Exercises.objects.update_or_create(name="Reverse Fly",category_id=4)
    models.Exercises.objects.update_or_create(name="Low Row(open)", category_id=4)
    models.Exercises.objects.update_or_create(name="Low Row(close)", category_id=4)
    models.Exercises.objects.update_or_create(name="Pull Over", category_id=4)
    models.Exercises.objects.update_or_create(name="Pull Over(Ban)", category_id=4)
    models.Exercises.objects.update_or_create(name="T Bar", category_id=4)
    models.Exercises.objects.update_or_create(name="Σκυφτή κωπηλατική με μπάρα", category_id=4)
    models.Exercises.objects.update_or_create(name="Κωπηλατική με μπάρα στον επικλινή", category_id=4)
    models.Exercises.objects.update_or_create(name="Reverse Push Up", category_id=4)
    models.Exercises.objects.update_or_create(name="Standing Row", category_id=4)
    models.Exercises.objects.update_or_create(name="Pull Over τροχαλίας", category_id=4)
    models.Exercises.objects.update_or_create(name="Pull Over τροχαλίας(open)", category_id=4)
    models.Exercises.objects.update_or_create(name="Pull Over τροχαλίας(Rope)", category_id=4)
    models.Exercises.objects.update_or_create(name="Dead lift", category_id=4)
    models.Exercises.objects.update_or_create(name="One Arm Row", category_id=4)
    models.Exercises.objects.update_or_create(name="One Arm Row με μπάρα(H.R)", category_id=4)
    models.Exercises.objects.update_or_create(name="Standing Row(Rope)", category_id=4)
    models.Exercises.objects.update_or_create(name="Πιέσεις Τρικεφάλων(smith)", category_id=5)
    models.Exercises.objects.update_or_create(name="Πιέσεις Τρικεφάλων(τροχαλία)", category_id=5)
    models.Exercises.objects.update_or_create(name="Γαλλικές Πιέσεις", category_id=5)
    models.Exercises.objects.update_or_create(name="Πιέσεις με σχοινί", category_id=5)
    models.Exercises.objects.update_or_create(name="Πιέσεις με λαβή", category_id=5)
    models.Exercises.objects.update_or_create(name="Πιέσεις με σχοινί(μονό)", category_id=5)
    models.Exercises.objects.update_or_create(name="Πιέσεις με ανάποδη λαβή", category_id=5)
    models.Exercises.objects.update_or_create(name="Kick Bach(Αλτήρα)", category_id=5)
    models.Exercises.objects.update_or_create(name="Kick Bach(τροχαλία)", category_id=5)
    models.Exercises.objects.update_or_create(name="Dips", category_id=5)
    models.Exercises.objects.update_or_create(name="Πιέσεις με ανάποδη λαβή(1 Χέρι)", category_id=5)
    models.Exercises.objects.update_or_create(name="Πιέσεις με 1 χέρι", category_id=5)
    models.Exercises.objects.update_or_create(name="Larry scott", category_id=6)
    models.Exercises.objects.update_or_create(name="Κάμψεις Δικεφάλων(τροχαλία)", category_id=6)
    models.Exercises.objects.update_or_create(name="Κάμψεις Δικεφάλων(Αλτήρες)", category_id=6)
    models.Exercises.objects.update_or_create(name="Κάμψεις Αυτοσυγκέντρωσης", category_id=6)
    models.Exercises.objects.update_or_create(name="Σφυριά", category_id=6)
    models.Exercises.objects.update_or_create(name="Σφυριά (ισομετρικά)", category_id=6)
    models.Exercises.objects.update_or_create(name="Σφυριά (Μπάρα)", category_id=6)
    models.Exercises.objects.update_or_create(name="Κάμψεις δικεφάλων ανάποδα(τροχαλία)", category_id=6)
    models.Exercises.objects.update_or_create(name="Κάμψεις δικεφάλων ανάποδα(Μπάρα)", category_id=6)
    models.Exercises.objects.update_or_create(name="Σφυριά στην τροχαλία(Σχοινί)", category_id=6)
    models.Exercises.objects.update_or_create(name="Crunches", category_id=7)
    models.Exercises.objects.update_or_create(name="Crunches(Bench)", category_id=7)
    models.Exercises.objects.update_or_create(name="Άρσεις Ποδιών", category_id=7)
    models.Exercises.objects.update_or_create(name="Άρσεις Ποδιών(Δίζυγο)", category_id=7)
    models.Exercises.objects.update_or_create(name="Άρσεις Ποδιών(Bench)", category_id=7)
    models.Exercises.objects.update_or_create(name="Kick the ball", category_id=7)
    models.Exercises.objects.update_or_create(name="Iso twist", category_id=7)
    models.Exercises.objects.update_or_create(name="Flatter kick", category_id=7)
    models.Exercises.objects.update_or_create(name="Criss cross", category_id=7)
    models.Exercises.objects.update_or_create(name="Plank", category_id=7)
    models.Exercises.objects.update_or_create(name="Side Plank", category_id=7)
    models.Exercises.objects.update_or_create(name="Plank 3-WAY", category_id=7)
    models.Exercises.objects.update_or_create(name="Heel touches", category_id=7)
    models.Exercises.objects.update_or_create(name="Crunches(Bosu)", category_id=7)
    models.Exercises.objects.update_or_create(name="Crunches(τροχαλία)", category_id=7)
    models.Exercises.objects.update_or_create(name="Crunches(τροχαλία - Σχοινί)", category_id=7)
    models.Exercises.objects.update_or_create(name="Climpers", category_id=7)
    models.Exercises.objects.update_or_create(name="Ραχιαίοι(Bench)", category_id=8)
    models.Exercises.objects.update_or_create(name="Ραχιαίοι", category_id=8)
    models.Exercises.objects.update_or_create(name="Superman", category_id=8)
    models.Exercises.objects.update_or_create(name="CV", category_id=9)
    models.Exercises.objects.update_or_create(name="Δρόμο / Treadmill", category_id=9)
    models.Exercises.objects.update_or_create(name="Ελλειπτικό / Ellyptical", category_id=9)
    models.Exercises.objects.update_or_create(name="Rowing Machine", category_id=9)
    models.Exercises.objects.update_or_create(name="Ποδήλατο/Bike", category_id=9)
    models.Exercises.objects.update_or_create(name="Wave", category_id=9)
    models.Exercises.objects.update_or_create(name="Rope", category_id=9)
    models.Exercises.objects.update_or_create(name="Jumping Jack", category_id=9)
    models.Exercises.objects.update_or_create(name="Skip", category_id=9)

from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views #import this


app_name = 'msfitcaregym'

urlpatterns = [
    path('home/',views.index,name='home'),
    path('dashboard/',views.dashboard,name='dashboard'),
    path('login/',views.Login,name='login'),
    path('logout/',views.Logout,name='logout'),
    path('hours/',views.WorkingHours,name='hours'),
    path('savehours/',views.saveHours,name='savehours'),
    path('pricing/',views.Pricing,name='pricing'),
    path ('removepricing/<int:pk>/', views.remove_pricing, name = 'removepricing'),
    path('removepricingphysio/<int:pk>/', views.remove_pricing_physio, name='removepricingphysio'),
    path('register/',views.Register, name='register'),
    path('registrationform/',views.RegistrationForm,name='registrationform'),
    path('userprogram/',views.UserProgram,name='userprogram'),
    path('programperday/',views.UserProgramPerDay,name='programperday'),
    path('displayuserprogram/',views.displayUserProgram, name='displayuserprogram'),
    path('displayprogramhistory/',views.displayProgramHistory,name='displayprogramhistory'),
    path('editprogramuser/',views.EditUserProgram,name='editprogramuser'),
    path('userprogramhistory/',views.UserProgramHistory,name='userprogramhistory'),
    path('userprogramperdayedit/<int:pk>/',views.UserProgramPerDayEdit1,name='programperdayedit1'),
    # path('programperdayedit/',views.UserProgramPerDayEdit, name='programperdayedit'),
    path('editday/<int:pk>/',views.EditDay,name='editday'),
    path('displayDay/<int:pk>/',views.displayDay,name='displayday'),
    path('addextraday/',views.addExtraDay,name='addextraday'),
    path('addpayment/',views.Payments,name='addpayments'),
    path('allpayments/',views.allPayments,name='allpayments'),
    path('editpayment/<int:pk>/',views.editPayments,name='editpayment'),
    path('userpayments/<int:pk>/',views.userPayments,name='userpayments'),
    path('paymentsuser/',views.paymentsUser,name='paymentsuser'),
    path('blockuser/<int:pk>/<str:acc>', views.BlockUser, name='blockuser'),
    path('checkann/',views.checkAnnouncements,name='checkannouncement'),
    path('savemodal/',views.saveModal,name='savemodal'),
    path('savemodaltest/', views.saveModaltest, name='savemodaltest'),
    path('removebodyparts/',views.removeBodyPart,name='removebodypart'),

    path('addcommentscard/',views.addCommentsCard,name='addcommentscard'),
    path('humanbody1/<int:pk>/',views.HumanBody1,name='humanbody1'),

    path('profile/',views.Profile,name='profile'),
    # path('humanbody/<int:pk>/',views.HumanBody,name='humanbody'),
    # path('displayhumanbody/<int:pk>/',views.DisplayHumanBody,name='displayhumanbody'),
    path('displayhumanbody1/<int:pk>/', views.DisplayHumanBody1, name='displayhumanbody1'),
    path('allexercises/',views.allExercises,name='allexercises'),
    path ('removeexercise/<int:pk>/', views.remove_exercise, name = 'removeexercise'),

    path('aboutus/',views.AboutUs, name='aboutus'),
    path('removeaboutus/<int:pk>/', views.remove_aboutus,name='removeaboutus'),
    path('removeprogram/<int:pk>/',views.remove_program,name='removeprogram'),
    path('removeprogramday/<int:pk>/',views.remove_program_day,name='removeprogramday'),
    path('announcements/',views.Announcements, name='announcements'),
    path('removeannouncement/<int:pk>/',views.remove_announcement,name = 'removeannouncement'),
    path('usersInfo/',views.UsersInfo,name='usersinfo'),
    path('blockuserInfo/<int:pk>/<str:acc>/',views.BlockUserInfo,name='usersinfoblock'),
    path('users/requests/<int:pk>/<str:acc>/', views.userRequestApprovalChange, name='usersRequestApprovalChange'),
    path('galery/',views.Galery,name='galery'),
    path('removegallery/<int:pk>/', views.remove_gallery, name='removegallery'),
    path('password/', views.change_password, name='change_password'),
    path("password_reset/", views.password_reset_request, name="password_reset"),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="password/password_reset_confirm.html"), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password/password_reset_complete.html'), name='password_reset_complete'),


    path('physio/slots/',views.physioSlotsJSON, name='physioSlots'),
    path('physio/slots/add/',views.addPhysioSlot, name='physioSlotsAdd'),
    path('physio/admin/',views.adminPhysioCalendar, name='adminPhysioCalendar'),
    path('calendar/addSlots/',views.addSlotsCalendar, name='addSlotsCalendar'),
    path('slots/add/',views.addSlots, name='addSlots'),
    path('gym/slots/',views.gymSlotsJSON, name='gymSlots'),
    path('calendar/user/<int:pk>/',views.userGymCalendar, name='userGymCalendar'),
    path('calendar/admin/<int:pk>/',views.adminGymCalendar, name='adminGymCalendar'),
    path('calendar/admin/slot/users',views.gymAdminReservations, name='gymAdminReservations'),
    path('calendar/user/addReservation/', views.gymUserAddReservation, name='gymUserAddReservation'),
    path('calendar/user/removeReservation/', views.gymUserRemoveReservation, name='gymUserRemoveReservation'),
    path('calendar/admin/removeReservation/', views.gymAdminRemoveReservation, name='gymAdminRemoveReservation'),
    path('calendar/admin/addReservation/', views.gymAdminAddReservation, name='gymAdminAddReservation'),
    path('physio/slot/update/', views.physioSlotUpdate, name='physioSlotUpdate'),
    path('physio/slot/delete/', views.physioSlotDelete, name='physioSlotDelete'),
    path('physio/user/delete/', views.physioAdminRemoveReservation, name='physioUserDelete'),
    path('physio/user/removeReservation/', views.physioUserRemoveReservation, name='physioUserRemoveReservation'),
    path('physio/admin/addUser/', views.physioAdminAddReservation, name='physioAdminUserAdd'),
    path('physio/user/addReservation/', views.physioUserAddReservation, name='physioUserAdd'),
    path('physio/user/',views.userPhysioCalendar, name='userPhysioCalendar'),
    path('daysClosed/',views.daysClosed, name='daysClosed'),
    path('addDayClosed/',views.addDayClosed, name='addDayClosed'),
    path('removeDayClosed/<int:repeating>/<int:pk>',views.removeDayClosed, name='removeDayClosed'),
    path('newCard/',views.physioNewCard, name='physioNewCard'),
    path('userCards/<int:pk>/',views.userCards, name='userCards'),

    path('adminRegistrationForm/',views.adminRegistrationForm,name='adminRegistrationForm'),
    path('displayForm/<int:pk>/',views.displayRegistrationForm,name='displayform'),

    path('adminReservations/<int:pk>/',views.adminReservations, name='adminReservations'),
    path('showReservations/',views.showReservations, name='showReservations'),
    path('userReservations/',views.userReservations, name='userReservations'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
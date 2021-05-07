import datetime

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.forms import inlineformset_factory, formset_factory,modelformset_factory
from . import models

class HomePageForm(forms.ModelForm):
    class Meta:
        model = models.HomePageText
        fields = ('text',)
        labels = {
            'text' : 'Κείμενο'
        }
class WorkingHoursForm(forms.ModelForm):
    class Meta:
        model = models.WorkingHours
        fields = ('day','time')
        labels = {
            'day' : 'Μέρα',
            'time': 'Ώρες',
        }
class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username','first_name','last_name','email')

    def __init__(self,*args,**kwargs):
        super(RegisterForm,self).__init__(*args,**kwargs)
        self.fields['username'] = forms.EmailField()

        # self.fields['username'].widget.attrs['placeholder'] = 'username'

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = models.UserProfile
        fields = [
            'birthday','job','Address','height','weight','goal','first_time_gym','smoking',
            'surgery','cardiac_test','package_choice','medicines','normal_blood_test',
            'headache','myosceletical_problems','epilepsy','other_problems','heart_problems',
            'stable_weight','approve','user','phone'
        ]
        labels = {
            'birthday':'Ημερομηνία Γέννησης',
            'job':'Επάγγελμα',
            'Address':'Διεύθυνση',
            'phone':'Τηλέφωνο',
            'height':'Ύψος',
            'weight':'Βάρος',
            'goal':'Στόχος',
            'first_time_gym':'Πρώτη Φορά σε Γυμναστήριο',
            'smoking':'Κάπνισμα',
            'surgery':'Χειρουργείο',
            'heart_problems':'Καρδιαγγειακά Προβήματα(Θρόμβωση,Υπέρταση,Υπόταση)',
            'medicines':'Φάρμακα(Τι είδος)',
            'normal_blood_test':'Αιματολογικές Εξετάσεις Φυσιολογικές',
            'cardiac_test':'Τεστ Κοπώσεως(Απαραίτητο άνω των 45-50 ετών',
            'epilepsy':'Επιληψία',
            'headache':'Πονοκεφάλοι',
            'myosceletical_problems':'Μυοσκελετικά Προβλήματα(Αυχένας,Μέση,Γόνατα κτλ). Είδος',
            'other_problems':'Παρακαλώ αναφέρετε οποιοδήποτε άλλο πρόβλημα υγείας',
            'stable_weight':'Σταθερό Βάρος',
            'package_choice':'Επιλογή Πακέτου',
            'approve':'Επιβεβαιώνω ότι είναι ορθά τα παραπάνω στοιχεία'
        }
    def __init__(self,*args,**kwargs):
        super(RegistrationForm,self).__init__(*args,**kwargs)
        self.fields['smoking'].widget = forms.CheckboxInput()
        self.fields['normal_blood_test'].widget = forms.CheckboxInput()
        self.fields['stable_weight'].widget = forms.CheckboxInput()
        self.fields['cardiac_test'].widget = forms.CheckboxInput()
        self.fields['approve'].widget = forms.CheckboxInput(attrs={'required':'required'})
        self.fields['phone'].widget.attrs['required'] = 'required'
        self.fields['birthday'].widget.attrs['required'] = 'required'
        self.fields['height'].widget.attrs['required'] = 'required'
        self.fields['weight'].widget.attrs['required'] = 'required'
        self.fields['user'].widget = forms.HiddenInput()
        cur_year = datetime.datetime.today().year
        year_range = tuple([i for i in range(cur_year - 90, cur_year)])
        self.fields['birthday'] = forms.DateField(label='Ημερομηνία Γέννησης',
                                                  widget=forms.SelectDateWidget(years=year_range))


class adminRegistrationForm(forms.ModelForm):
    class Meta:
        model = models.UserProfile
        fields = [
            'first_name', 'last_name', 'birthday','job','Address','height','weight','goal','first_time_gym','smoking',
            'surgery','cardiac_test','package_choice','medicines','normal_blood_test',
            'headache','myosceletical_problems','epilepsy','other_problems','heart_problems',
            'stable_weight','phone'
        ]
        labels = {
            'first_name':'Όνομα',
            'last_name':'Επίθετο',
            'birthday':'Ημερομηνία Γέννησης',
            'job':'Επάγγελμα',
            'Address':'Διεύθυνση',
            'phone':'Τηλέφωνο',
            'height':'Ύψος',
            'weight':'Βάρος',
            'goal':'Στόχος',
            'first_time_gym':'Πρώτη Φορά σε Γυμναστήριο',
            'smoking':'Κάπνισμα',
            'surgery':'Χειρουργείο',
            'heart_problems':'Καρδιαγγειακά Προβήματα(Θρόμβωση,Υπέρταση,Υπόταση)',
            'medicines':'Φάρμακα(Τι είδος)',
            'normal_blood_test':'Αιματολογικές Εξετάσεις Φυσιολογικές',
            'cardiac_test':'Τεστ Κοπώσεως(Απαραίτητο άνω των 45-50 ετών',
            'epilepsy':'Επιληψία',
            'headache':'Πονοκεφάλοι',
            'myosceletical_problems':'Μυοσκελετικά Προβλήματα(Αυχένας,Μέση,Γόνατα κτλ). Είδος',
            'other_problems':'Παρακαλώ αναφέρετε οποιοδήποτε άλλο πρόβλημα υγείας',
            'stable_weight':'Σταθερό Βάρος',
            'package_choice':'Επιλογή Πακέτου',
        }
    def __init__(self,*args,**kwargs):
        super(adminRegistrationForm,self).__init__(*args,**kwargs)
        self.fields['smoking'].widget = forms.CheckboxInput()
        self.fields['normal_blood_test'].widget = forms.CheckboxInput()
        self.fields['stable_weight'].widget = forms.CheckboxInput()
        self.fields['cardiac_test'].widget = forms.CheckboxInput()
        self.fields['phone'].widget.attrs['required'] = 'required'
        self.fields['birthday'].widget.attrs['required'] = 'required'
        self.fields['height'].widget.attrs['required'] = 'required'
        self.fields['weight'].widget.attrs['required'] = 'required'
        cur_year = datetime.datetime.today().year
        year_range = tuple([i for i in range(cur_year - 90, cur_year)])
        self.fields['birthday']=forms.DateField(label='Ημερομηνία Γέννησης',widget=forms.SelectDateWidget(years=year_range))

class ProfileForm(forms.ModelForm):
    class Meta:
        model = models.UserProfile
        fields = [
            'birthday','job','Address','height','weight','goal','phone'
        ]
        labels = {
            'birthday':'Ημερομηνία Γέννησης',
            'job':'Επάγγελμα',
            'Address':'Διεύθυνση',
            'phone':'Τηλέφωνο',
            'height':'Ύψος',
            'weight':'Βάρος',
            'goal':'Στόχος',
            'package_choice':'Επιλογή Πακέτου',
        }
    def __init__(self,*args,**kwargs):
        super(ProfileForm,self).__init__(*args,**kwargs)

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username','first_name','last_name','email')
        labels = {
            'username':'Διεύθυνση Email'
        }

    def __init__(self,*args,**kwargs):
        super(UserForm,self).__init__(*args,**kwargs)
        self.fields['username'].widget.attrs['readonly'] = 'readonly'
        self.fields['username'].help_text = None

class AboutUsForm(forms.ModelForm):
    class Meta:
        model = models.AboutUs
        fields = ['name','details','photo']
        labels = {
            'name':'Όνομα',
            'details': 'Πληροφορίες',
            'photo':'Φωτογραφία'
        }
    def __init__(self,*args,**kwargs):
        super(AboutUsForm,self).__init__(*args,**kwargs)
        self.fields['photo'].widget.attrs['required'] = 'required'

class PackageForm(forms.ModelForm):
    class Meta:
        model = models.Packages
        fields = ['duration','price','description','special_offer']
        labels = {
            'duration': 'Διάρκεια',
            'price': 'Τιμή',
            'description':'Περιγραφή',
            'special_offer':'Προσφορά'
        }
    def __init__(self,*args,**kwargs):
        super(PackageForm,self).__init__(*args,**kwargs)
        self.fields['special_offer'].widget = forms.CheckboxInput()

class PhysioPricesForm(forms.ModelForm):
    class Meta:
        model = models.PhysioPrices
        fields = ['duration','price','description']
        labels = {
            'duration': 'Τίτλος',
            'price': 'Τιμή',
            'description':'Περιγραφή',
        }
    def __init__(self,*args,**kwargs):
        super(PhysioPricesForm,self).__init__(*args,**kwargs)


class PaymentsForm(forms.ModelForm):
    class Meta:
        model = models.Payments
        fields = ['user','pay_from','pay_until','package','price']
        labels = {
            'user':'Χρήστης',
            'package':'Πακέτο',
            'price':'Ποσό',
            'pay_from':'Από',
            'pay_until':'Μέχρι'
        }
    def __init__(self,*args,**kwargs):
        super(PaymentsForm,self).__init__(*args,**kwargs)
        self.fields['pay_from'].widget = forms.TextInput (attrs = {'type': 'date'})
        self.fields['pay_until'].widget = forms.TextInput (attrs = {'type': 'date'})
        self.fields['user'].queryset = models.UserProfile.objects.filter(accountStatus__in=['Accepted', 'NoUser'])


class AnnouncementsForm(forms.ModelForm):
    class Meta:
        model = models.Announcements
        fields = ['title','details']
        labels = {
            'title':'Τίτλος',
            'details':'Περιγραφή'
        }
    def __init__(self,*args,**kwargs):
        super(AnnouncementsForm,self).__init__(*args,**kwargs)

class GalleryForm(forms.ModelForm):
    class Meta:
        model = models.Gallery
        fields = ['title','details','photo']
        labels = {
            'title':'Τίτλος',
            'details':'Περιγραφή',
            'photo':'Φωτογραφία'
        }
    def __init__(self,*args,**kwargs):
        super(GalleryForm,self).__init__(*args,**kwargs)
        self.fields['photo'].widget.attrs['required'] = 'required'

class ProgramUserForm(forms.ModelForm):
    class Meta:
        model = models.ProgramUser
        fields = ['goal','user',]
        labels = {
            'goal':'Στόχος',
            'user':'Χρήστης'
        }
    def __init__(self,*args,**kwargs):
        super(ProgramUserForm,self).__init__(*args,**kwargs)
        self.fields['goal'].widget.attrs['required'] = 'required'
        self.fields['user'].widget.attrs['required'] = 'required'
        self.fields['user'].queryset = models.UserProfile.objects.filter(accountStatus__in=['Accepted', 'NoUser'])



class ExersicePerDayForm(forms.ModelForm):
    class Meta:
        model = models.ExercisesPerDate
        fields = ['id_exercises','id_program_Date','sets','times','color','negative']
        labels = {
            'id_exercises':'Άσκηση',
            'id_program_Date':'Μέρα',
            'sets':'Σετς',
            'times':'Επαναλήψεις',
            'color':'Χρώμα',
            'negative': 'Αρνητικές Επαναλήψεις'
        }
    def __init__(self,*args,**kwargs):
        super(ExersicePerDayForm,self).__init__(*args,**kwargs)
        self.fields['id_exercises'].widget.attrs['required'] = 'required'
        self.fields['id_exercises'].widget.attrs = {
            'onload' : "select(this.id)",
            }
        self.fields['color'].widget.attrs['class'] = "jscolor"
        self.fields['color'].widget.attrs['value'] = '#000000'
        self.fields['negative'].widget = forms.CheckboxInput()


class ProgramDayForm(forms.ModelForm):
    class Meta:
        model = models.ProgramDates
        fields = ['title','program',]
        labels = {
            'title':'Μέρα',
            'program':'id program'
        }
    def __init__(self,*args,**kwargs):
        super(ProgramDayForm,self).__init__(*args,**kwargs)
        self.fields['title'].widget.attrs['required'] = 'required'


ProgramFormset = formset_factory(ExersicePerDayForm, extra=1)
ProgramFormsetEdit = modelformset_factory(models.ExercisesPerDate,ExersicePerDayForm,can_delete=True,extra=1)


class newCardForm(forms.ModelForm):
    class Meta:
        model = models.PhysioCard
        fields = ['title','user']
        labels={
            'title':'Τίτλος',
            'user':"Χρήστης"
        }

    def __init__(self,*args,**kwargs):
        super(BodyPartForm,self).__init__(*args,**kwargs)
        self.fields['user'].queryset = models.UserProfile.objects.filter(accountStatus__in=['Accepted', 'NoUser'])


class BodyPartForm(forms.ModelForm):
    class Meta:
        model = models.BodyParts
        fields = ['physio_card','color','details','circle_id','x','y']

    def __init__(self,*args,**kwargs):
        super(BodyPartForm,self).__init__(*args,**kwargs)

class ExerciseForm(forms.ModelForm):
    class Meta:
        model = models.Exercises
        fields = ['name','category']
        labels = {
            'name':'Όνομα Άσκησης',
            'category':'Κατηγορία'
        }
    def __init__(self,*args,**kwargs):
        super(ExerciseForm,self).__init__(*args,**kwargs)
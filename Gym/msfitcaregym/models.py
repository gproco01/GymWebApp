from django.db import models
from django.contrib.auth.models import User
from django.db.models import CASCADE
import datetime


# Create your models here.
class HomePageText(models.Model):
    text = models.TextField(max_length=5000, null= True, blank=True)
    def __str__(self):
        return '{}'.format(self.text)

class WorkingHours(models.Model):
    id_day = models.AutoField(primary_key = True)
    day = models.CharField(max_length=100, null=True, blank=True)
    time = models.CharField(max_length=200, null=True, blank=True)

class Packages(models.Model):
    id_package = models.AutoField(primary_key = True)
    price = models.PositiveIntegerField(null=True, blank=True)
    duration = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(max_length=500, null=True,blank=True)
    special_offer = models.BooleanField(null=True, blank=True, default = False)
    def __str__(self):
        return '{} : {}'.format(self.duration, self.price)

class PhysioPrices(models.Model):
    id_package = models.AutoField(primary_key = True)
    price = models.PositiveIntegerField(null=True, blank=True)
    duration = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(max_length=500, null=True,blank=True)
    def __str__(self):
        return '{} : {}'.format(self.duration, self.price)

class UserProfile(models.Model):
    goals = {
        ('Υγεία','Υγεία'),
        ('Μείωση Βάρους', 'Μύωση Βάρους'),
        ('Αύξηση Βάρους','Αύξηση Βάρους'),
        ('Αποκατάσταση Τραυματισμών','Αποκατάσταση Τραυματισμών'),
        ('Συντήρηση','Συντήρηση'),
    }
    status_selection = [
        ('Request', 'Request'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
        ('Revoke', 'Revoke'),
        ('NoUser', 'NoUser'),
    ]
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=CASCADE,null=True, blank= True)
    birthday= models.DateField(null=True, blank= True)
    job = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length= 15, null=True, blank=True)
    Address = models.CharField(max_length=200, null=True,blank=True)
    height = models.PositiveIntegerField(null=True,blank=True)
    weight = models.FloatField(null=True, blank=True)
    goal = models.CharField(max_length=100, choices=goals, null=True,blank=True)
    first_time_gym = models.BooleanField(null=True, blank=True)
    smoking = models.BooleanField(null=True, blank=True)
    surgery = models.CharField(max_length=300, blank=True, null=True)
    heart_problems = models.CharField(max_length=300, blank=True, null=True)
    medicines = models.CharField(max_length=300, blank=True, null=True)
    normal_blood_test = models.BooleanField(blank=True, null=True)
    cardiac_test = models.BooleanField(blank=True,null=True)
    epilepsy = models.CharField(max_length=200, blank=True, null=True)
    headache = models.CharField(max_length=200, blank=True, null=True)
    myosceletical_problems = models.CharField(max_length=300, null=True, blank=True)
    other_problems = models.CharField(max_length=300, null=True,blank=True)
    stable_weight = models.BooleanField(null=True, blank=True)
    approve = models.BooleanField(null=True, blank=True)
    package_choice = models.ForeignKey('Packages', on_delete=CASCADE, null=True, blank=True)
    accountStatus = models.CharField(max_length=30, choices=status_selection, default="Request", null=False, blank=False)
    checkann = models.DateTimeField(null=True,blank=True)
    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)

class Type(models.Model):
    id_type = models.AutoField(primary_key = True)
    Title = models.CharField(max_length=200, null=True,blank=True)
    total_persons = models.PositiveIntegerField(null=True,blank=True)
    active = models.BooleanField(null=True,blank=True)

class Slots(models.Model):
    id_slot = models.AutoField(primary_key = True)
    type = models.ForeignKey('Type', on_delete=CASCADE)
    day=models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    valid_from = models.DateField()
    valid_to = models.DateField(null=True,blank=True)

class GymReservations(models.Model):
    id_reservation = models.AutoField(primary_key = True)
    date = models.DateField()
    user = models.ForeignKey('UserProfile',on_delete=CASCADE)
    time = models.ForeignKey('Slots', on_delete=CASCADE)
    type = models.ForeignKey('Type', on_delete=CASCADE)
    attendance = models.BooleanField(default=True)

class daysClosed(models.Model):
    id_day = models.AutoField(primary_key=True)
    date = models.DateField()

class repeatingDaysClosed(models.Model):
    id_day = models.AutoField(primary_key=True)
    month=models.PositiveSmallIntegerField()
    day = models.PositiveSmallIntegerField()
    valid_from = models.DateField()
    valid_to = models.DateField(null=True,blank=True)

class PhysioReservations(models.Model):
    id_reservation = models.AutoField(primary_key = True)
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    user = models.ForeignKey('UserProfile',null=True, blank=True ,on_delete=CASCADE)
    cancel = models.BooleanField(default=False)

class PhysioCard(models.Model):
    id_card = models.AutoField(primary_key = True)
    title= models.CharField(max_length=200)
    user = models.ForeignKey('UserProfile',on_delete=CASCADE)
    comments = models.TextField(null=True, blank=True)

class BodyParts(models.Model):
    id_part = models.AutoField(primary_key = True)
    physio_card = models.ForeignKey('PhysioCard',on_delete=CASCADE)
    circle_id = models.CharField(max_length=500,null=True, blank=True)
    partid = models.CharField(max_length=500, null=True, blank=True)
    x = models.FloatField(blank=True,null=True)
    y = models.FloatField(blank=True,null = True)
    color = models.CharField(max_length=500, null=True,blank=True)
    details = models.TextField(null=True, blank=True)

class Payments(models.Model):
    id_payment = models.AutoField(primary_key = True)
    user = models.ForeignKey('UserProfile',on_delete=CASCADE)
    pay_from = models.DateField(null=True, blank=True)
    pay_until = models.DateField(null=True, blank=True)
    price = models.FloatField(null=True, blank=True)
    package = models.ForeignKey('Packages', on_delete=CASCADE)

class ProgramUser(models.Model):
    goals = {
        ('Υγεία', 'Υγεία'),
        ('Μύωση Βάρους', 'Μύωση Βάρους'),
        ('Αύξηση Βάρους', 'Αύξηση Βάρους'),
        ('Αποκατάσταση Τραυματισμών', 'Αποκατάσταση Τραυματισμών'),
        ('Συντήρηση', 'Συντήρηση'),
    }
    id_program = models.AutoField(primary_key = True)
    user = models.ForeignKey('UserProfile', on_delete=CASCADE)
    date = models.DateField(null=True, blank=True,default= datetime.date.today())
    goal = models.CharField(max_length=300,choices=goals)

class Categories(models.Model):
    id_category = models.AutoField(primary_key = True)
    name = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return '{}'.format( self.name)

class Exercises(models.Model):
    id_exercise = models.AutoField(primary_key = True)
    name = models.CharField(max_length=300, null=True, blank=True)
    category = models.ForeignKey('Categories', on_delete=CASCADE)

    def __str__(self):
        return '{}'.format( self.name)

class ProgramDates(models.Model):
    days = {
        ('Μέρα 1','Μέρα 1'),
        ('Μέρα 2', 'Μέρα 2'),
        ('Μέρα 3', 'Μέρα 3'),
        ('Μέρα 4', 'Μέρα 4'),
        ('Μέρα 5', 'Μέρα 5'),
        ('Μέρα 6', 'Μέρα 6'),
        }
    id_program_date = models.AutoField(primary_key = True)
    title = models.CharField(max_length=200,choices=days,null=True, blank=True)
    program = models.ForeignKey('ProgramUser', on_delete=CASCADE)

class ExercisesPerDate(models.Model):
    id_exercises_date = models.AutoField(primary_key = True)
    id_program_Date = models.ForeignKey('ProgramDates',on_delete=CASCADE,null=True,blank=True)
    id_exercises = models.ForeignKey('Exercises', on_delete=CASCADE)
    sets = models.PositiveIntegerField(null=True, blank=True)
    times = models.PositiveIntegerField(null=True, blank=True)
    color = models.CharField(max_length = 100,null = True, blank = True,default = '#000000')
    negative = models.BooleanField(null = True, blank = True, default = False)

class Announcements(models.Model):
    id_announcement = models.AutoField(primary_key = True)
    title = models.CharField(max_length= 100, null=True, blank=True)
    details = models.TextField(max_length=10000, null=True,blank=True)
    submited_date = models.DateTimeField(default = datetime.datetime.now())

class AboutUs(models.Model):
    id_about = models.AutoField(primary_key = True)
    name = models.CharField(max_length = 200, null = True, blank = True)
    details = models.TextField(max_length = 10000, null = True, blank = True)
    photo = models.ImageField(upload_to = 'about_us',blank = True,null = True)

class Gallery(models.Model):
    id_gallery = models.AutoField(primary_key = True)
    title = models.CharField(max_length=300, null=True, blank=True)
    details = models.TextField(max_length=10000, null=True, blank = True)
    photo = models.ImageField(upload_to='gallery', null=True, blank=True)
    reservation=models.ForeignKey("Type",on_delete=CASCADE,null=True,blank=True)
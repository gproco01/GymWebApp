from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Type)
admin.site.register(models.Slots)
admin.site.register(models.Packages)
admin.site.register(models.Payments)
admin.site.register(models.ProgramUser)
admin.site.register(models.ProgramDates)
admin.site.register(models.Categories)
admin.site.register(models.Exercises)
admin.site.register(models.ExercisesPerDate)
admin.site.register(models.GymReservations)
admin.site.register(models.PhysioCard)
admin.site.register(models.PhysioReservations)
admin.site.register(models.BodyParts)
admin.site.register(models.UserProfile)
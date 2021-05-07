from django.core.management.base import BaseCommand
from msfitcaregym.views import addhours,addCategories,addExercises

class Command(BaseCommand):
    help="Add hours to database"

    def handle(self, *args, **kwargs):
        addhours()
        addCategories()
        addExercises()
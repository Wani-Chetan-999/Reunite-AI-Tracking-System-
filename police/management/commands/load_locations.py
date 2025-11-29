from django.core.management.base import BaseCommand
import csv
from police.models import State, District, Taluka

class Command(BaseCommand):
    help = 'Load states, districts, talukas from CSV'

    def handle(self, *args, **kwargs):
        with open('locations.csv') as f:
            reader = csv.DictReader(f)
            for row in reader:
                state, _ = State.objects.get_or_create(name=row['state'])
                district, _ = District.objects.get_or_create(state=state, name=row['district'])
                Taluka.objects.get_or_create(district=district, name=row['taluka'])
        self.stdout.write(self.style.SUCCESS('Locations loaded successfully'))
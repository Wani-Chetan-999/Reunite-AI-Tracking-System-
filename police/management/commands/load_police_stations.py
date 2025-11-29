from django.core.management.base import BaseCommand
import csv
from police.models import Taluka, PoliceStation

class Command(BaseCommand):
    help = 'Load or update police stations from CSV'

    def handle(self, *args, **kwargs):
        with open('police_stations.csv') as f:
            reader = csv.DictReader(f)
            for row in reader:
                taluka_obj = Taluka.objects.get(name=row['taluka'])
                ps, created = PoliceStation.objects.get_or_create(
                    taluka=taluka_obj,
                    name=row['police_station'],
                )
                # Update email in case it's changed
                ps.email = row.get('email', '')
                ps.save()

        self.stdout.write(self.style.SUCCESS('Police stations loaded/updated successfully'))
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Create a default admin user if it doesn't exist"

    def handle(self, *args, **kwargs):
        User = get_user_model()
        username = "admin"
        password = "admin123"
        email = "admin@example.com"

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS("Default admin created."))
        else:
            self.stdout.write("Default admin already exists.")

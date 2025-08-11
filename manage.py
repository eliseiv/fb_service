import os
import sys
from django.core.management import execute_from_command_line


def init_django():
    import django
    from django.conf import settings

    if settings.configured:
        return

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.infrastructure.settings')
    django.setup()


if __name__ == "__main__":
    init_django()
    execute_from_command_line(sys.argv)

import os, sys

sys.path.append(os.path.dirname(__file__))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "docucomment.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

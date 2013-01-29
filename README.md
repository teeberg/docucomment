This is a web service that allows people to post pdfs and to comment their pages.

This is alpha almost untested software. Comes with no warranty. Needs security review.

INSTALL
=======

Dependencies (sudo apt-get install):
* python
* python-django
* sqlite3

Navigate to some place where you want to put the library
* git clone https://github.com/fuligginoso/docucomment
* cd docucomment
* ./manage.py syncdb
* chmod a+wr database
* chmod a+wr database/docucomment.db

to test it:
* python manage.py runserver 0.0.0.0:8000

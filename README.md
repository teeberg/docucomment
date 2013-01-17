This is a web service that allows people to post pdfs and to comment their pages.

This is alpha almost untested software. Comes with no warranty. Needs security review.

INSTALL
=======

Dependencies (sudo apt-get install):
* python
* python-django
* sqlite3

Navigate to some place where you want to put the library
git clone https://github.com/fuligginoso/docucomment
cd docucomment
python manage.py syncdb

to test it:
python manage.py runserver

You'll need to run a real server. There are many ways to do it. The keyword is django, the python framework I used to program this.

https://docs.djangoproject.com/en/1.4/
https://docs.djangoproject.com/en/1.4/howto/deployment/

I installed it on apache:
https://docs.djangoproject.com/en/1.4/howto/deployment/wsgi/modwsgi/

Dependencies
* apache2
* libapache2-mod-wsgi
* libapache2-mod-python

The basic configuration they give is

WSGIScriptAlias / /path/to/mysite.com/mysite/wsgi.py
WSGIPythonPath /path/to/mysite.com

<Directory /path/to/mysite.com/mysite>
<Files wsgi.py>
Order deny,allow
Allow from all
</Files>
</Directory>

but actually to make it work I had to copy wsgi.py up one level, so point to that one

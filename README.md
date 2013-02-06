This is a web service that allows people to post pdfs and to comment their pages, which is especially useful for sharing presentation slides and collaboratively comment or work on them.

This software is nowhere near ready for productional use. We use it ourselves and it seems to work already very well. Feel free to try it out and give us feedback! We'd certainly appreciate to hear from you!

INSTALL
===

### Dependencies (sudo apt-get install):
* python
* python-django
* sqlite3

### Navigate to some place where you want to put the library:
```bash
git clone https://github.com/fuligginoso/docucomment
cd docucomment
./manage.py syncdb
chmod a+wr database
chmod a+wr database/docucomment.db
```

### Run it!
```bash
./manage.py runserver 0.0.0.0:8000
```

0.0.0.0 binds to all interfaces, i.e. makes you accessible from the outside.
Leave it out if you want to run a local server.

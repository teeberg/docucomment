#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "docucomment.settings")

	from django.core.management import execute_from_command_line

	# default command line if no argument given
	commandline = "runserver 0.0.0.0:8000"
	if len(sys.argv) == 1:
		sys.argv.extend(commandline.split(' '))

	execute_from_command_line(sys.argv)

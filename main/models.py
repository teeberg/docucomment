from django.db import models
from main.parser import Parser

class Summary(models.Model):
	name = models.CharField(max_length=200)
	creation_date = models.DateTimeField('date created')
	deleted = models.BooleanField()

class Section(models.Model):
	name = models.CharField(max_length=200)
	index = models.IntegerField()
	summary = models.ForeignKey(Summary)
	creation_date = models.DateTimeField('date created')
	section = models.TextField()
	deleted = models.BooleanField()

	def section_parsed(self):
		return Parser.parse(self.section)

class Document(models.Model):
	name = models.CharField(max_length=200)
	file = models.FileField(upload_to='files')
	upload_date = models.DateTimeField('date uploaded')
	hash = models.CharField(max_length=200)
	public = models.BooleanField(default=True)
	deleted = models.BooleanField()

class Comment(models.Model):
	nickname = models.CharField(max_length=32)
	comment = models.TextField()
	document = models.ForeignKey(Document)
	creation_date = models.DateTimeField('date created')
	page = models.IntegerField()
	deleted = models.BooleanField()

	def comment_parsed(self):
		return Parser.parse(self.comment)
		

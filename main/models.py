from django.db import models

# Create your models here.
class Document(models.Model):
	name = models.CharField(max_length=200)
	file = models.FileField(upload_to='files')
	upload_date = models.DateTimeField('date uploaded')
	hash = models.CharField(max_length=200)
	public = models.BooleanField()

class Comment(models.Model):
	nickname = models.CharField(max_length=32)
	comment = models.TextField()
	document = models.ForeignKey(Document)
	creation_date = models.DateTimeField('date created')
	page = models.IntegerField()

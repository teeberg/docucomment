from django.db import models
import re

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
	deleted = models.BooleanField()
	def comment_parsed(self):
		res = self.comment
		link_regex = re.compile(r"\[\[([^\]/]+)(\/(\d+))?\]\]")
		def make_ahref(match):
			pdf, pagepart, page = match.groups()
			ds = Document.objects.filter(name=pdf)
			if len(ds) >= 1:
				d = ds[0]
				if page == None:
					return '<a href="/document/%s">%s</a>' % (d.hash, d.name)
				else:
					return '<a href="/document/%s?page=%s">%s (page %s)</a>' % (d.hash, page, d.name, page)
			return match.group(0)
		res = link_regex.sub(make_ahref, res)
		#res = link_regex.sub("bla", res)
		return res


from django.db import models
from django.utils.html import escape
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
		res = escape(self.comment)
		link_regex = re.compile(r"\[\[([^\]/\|]+)(\/(\d+))?(?:\|([^\]]+))?\]\]")
		def make_ahref(match):
			d = match.groups()
			print d
			pdf, pagepart, page, title = match.groups()
			ds = Document.objects.filter(name=pdf)
			if len(ds) >= 1:
				d = ds[0]
				if page == None:
					if title == None:
						title = d.name
					return '<a href="/document/%s">%s</a>' % (d.hash, title)
				else:
					if title == None:
						title = "{} (page {})".format(d.name, page)
					return '<a href="/document/%s?page=%s">%s</a>' % (d.hash, page, title)
			return match.group(0)
		res = link_regex.sub(make_ahref, res)
		return res


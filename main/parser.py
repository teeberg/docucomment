from django.utils.html import escape
import re
import string
import main.models

class Parser:
	@staticmethod
	def parse(string, space):
		res = escape(string)

		# Urls
		url_regex = re.compile(r"\[(http:\/\/([^]]+))\]")
		def make_url(match):
			return '<a href="'+match.group(1)+'">'+match.group(2)+'</a>'
		res = url_regex.sub(make_url, res)
			

		# Internal links
		link_regex = re.compile(r"\[\[([^\]/\|]+)(\/(\d+))?(?:\|([^\]]+))?\]\]")
		def make_ahref(match):
			d = match.groups()
			pdf, pagepart, page, title = match.groups()
			ds = main.models.Document.objects.filter(space=space, name=pdf)
			if len(ds) >= 1:
				d = ds[0]
				if page == None:
					if title == None:
						title = d.name
					return '<a class="document-link" data-document-hash="%s" data-document-name="%s" data-page=%s href="/space/%s/document/%s">%s</a>' % (d.hash, d.name, 0, space.name, d.hash, title)
				else:
					if title == None:
						title = "{} (page {})".format(d.name, page)
					return '<a class="document-link" data-document-hash="%s" data-document-name="%s" data-page=%s href="/space/%s/document/%s?page=%s">%s</a>' % (d.hash, d.name, page, space.name, d.hash, page, title)
			return match.group(0)
		res = link_regex.sub(make_ahref, res)
		block_regex = re.compile(r"\[(\w+)(( \w+=\w+)*)\]")
		def make_block(match):
			block_handlers = {'code': Parser.codeblock}
			if match.group(1) in block_handlers:
				args = {}
				if match.group(2) != "":
					for param in match.group(2)[1:].split(" "):
						args[param.split("=")[0]] = param.split("=")[1]
				return Parser.codeblock(args)
			return match.group(0)
		res = block_regex.sub(make_block, res)
		
		block_end_regex = re.compile(r"\[\/(\w+)\]")
		def make_block_end(match):
			blocks = {"code"}
			if match.group(1) in blocks:
				return "</%s>" % match.group(1)
			return match.group(0)
		res = block_end_regex.sub(make_block_end, res)
		return res

	@staticmethod
	def codeblock(args):
		if ("lang" in args):
			lang = args['lang']
		else:
			lang = 'text'
		return '<code class="brush: %s;">' % lang 

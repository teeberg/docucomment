from django import forms
from django.http import Http404, HttpResponse
from django.core.servers.basehttp import FileWrapper
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Max
from django.utils import simplejson
from django.utils.html import escape, strip_tags
from django.shortcuts import render_to_response, redirect
from django.contrib.auth.forms import AuthenticationForm
from main.models import Document, Comment, Summary, Section
from datetime import datetime, timedelta
from hashlib import sha1
from mimetypes import guess_type
import sys
import traceback

# Create your views here.

def home(request):
	if request.method == 'POST':
		if request.POST['action'] == "post-document":
			uploadForm = DocumentUploadForm(request.POST, request.FILES)
			if (uploadForm.is_valid()):
				file = request.FILES['file']
				hash = sha1("blob " + str(file.size) + "\0" + file.read()).hexdigest()
				ds = Document.objects.filter(hash=hash)
				if (len(ds) == 0):
					d = uploadForm.save(commit=False)
					d.hash = hash
					d.name = file.name
					d.upload_date = datetime.now()
					d.save()
				return redirect("/document/" + hash)
		elif request.POST['action'] == "post-summary":
			summaryForm = SummaryForm(request.POST)
			if (summaryForm.is_valid()):
				s = summaryForm.save(commit=False)
				s.creation_date = datetime.now()
				s.save()
				return redirect("/summary/" + str(s.id))

	uploadForm = DocumentUploadForm()
	summaryForm = SummaryForm()
	
	return render_to_response('main/home.html', {"page": "home", "documents": Document.objects.order_by('name').all(), "uploadForm": uploadForm, "summaries": Summary.objects.order_by('name').all(), "summaryForm": summaryForm})

def send_file(request, hash):
	ds = Document.objects.filter(hash=hash)
	if len(ds) == 0:
		raise Http404
	d = ds[0]
	wrapper = FileWrapper(d.file)
	response = HttpResponse(wrapper, content_type=guess_type(d.name)[0])
	response['Content-Length'] = d.file.size
	response['Content-Disposition'] = "attachment; filename=\"%s\"" % d.name
	return response

def summary(request, id):
	try:
		s = Summary.objects.get(pk=id)
	except ObjectDoesNotExist:
		raise Http404
	if s == None:
		raise Http404
	sectionForm = SectionForm()
	return render_to_response('main/summary.html', {"summary": s, "sectionForm": sectionForm})

def document(request, hash):
	ds = Document.objects.filter(hash=hash)
	if len(ds) == 0:
		raise Http404
	try:
		page = int(request.GET['page']) if 'page' in request.GET else 1
	except:
		return redirect("/document/"+hash)
	initial = {}
	if "nickname" in request.COOKIES:
		initial["nickname"] = request.COOKIES["nickname"]
	form = CommentForm(initial=initial)
	return render_to_response('main/document.html', {"document": ds[0], 'commentForm': form, 'page': page})

def sections(request, summary):
	try:
		su = Summary.objects.get(pk=summary)
	except ObjectDoesNotExist:
		raise Http404
	if su == None:
		raise Http404
	sections = Section.objects.filter(summary=su, deleted=False).order_by("index")
	ss = {}
	for section in sections:
		s = {"id": section.id, "name": section.name, "section_plain": section.section, "section": section.section_parsed(), "index": section.index}
		ss[section.index] = s
	return HttpResponse(simplejson.dumps(ss))

def comments(request, hash=None, page=None):
	if hash == None:
		comments = Comment.objects.filter(deleted=False).order_by('-creation_date')
	else:
		ds = Document.objects.filter(hash=hash)
		if len(ds) == 0:
			raise Http404
		d = ds[0]
		comments = Comment.objects.filter(document=d, page=page, deleted=False)
	cs = []
	for comment in comments:
		c = {"id": comment.id, "nickname": escape(comment.nickname), "nickname_plain": comment.nickname, "comment": comment.comment_parsed(), "comment_plain": comment.comment, "page": comment.page, "document_public": comment.document.public}
		cs.append(c)
		if comment.document.public:
			c["document_hash"] = comment.document.hash
	return HttpResponse(simplejson.dumps(cs))

def renamedocument(request, hash):
	ret = {'status': 1}
	d = Document.objects.get(hash=hash)
	if d == None:
		ret['message'] = 'No document exists with this hash.'
	elif 'name' not in request.POST:
		ret['message'] = 'No new name supplied.'
	else:
		try:
			d.name = request.POST['name']
			d.save()
			ret['status'] = 0
			ret['name_escaped'] = escape(d.name)
		except Exception as ex:
			ret['message'] = 'An exception was thrown. Please notify an administrator.'
			traceback.print_exc(file=sys.stdout)
	return HttpResponse(simplejson.dumps(ret))

def comment(request, hash, page):
	if request.method == 'POST':
		post = request.POST.copy()
		post.update({'nickname': strip_tags(request.POST['nickname'])})
		ds = Document.objects.filter(hash=hash)
		if (len(ds) == 0):
			raise Http404
		d = ds[0]
		if post.has_key('id') and len(post['id']) > 0:
			commentForm = CommentForm(post, instance=Comment.objects.get(pk=int(post['id'])))
			if commentForm.is_valid():
				commentForm.save()
				return HttpResponse(simplejson.dumps({"status": "ok"}))
		else:
			commentForm = CommentForm(post)
			if commentForm.is_valid():
				c = commentForm.save(commit=False)
				c.creation_date = datetime.now()
				c.document = d
				c.page = page
				c.save()
				response = HttpResponse(simplejson.dumps({"status": "ok"}))
				response.set_cookie("nickname", c.nickname)
				return response
	raise Http404

def section(request, summary):
	try:
		su = Summary.objects.get(pk=summary)
	except ObjectDoesNotExist:
		raise Http404
	if su == None:
		raise Http404
	if request.method == "POST":
		if request.POST["summary_id"] != summary:
			return HttpResponse(simplejson.dumps({"status": "error", "message": "summary id doesn't correspond"}))
		if "id" in request.POST and len(request.POST['id']) > 0:
			sectionForm = SectionForm(request.POST, instance=Section.objects.get(pk=int(request.POST['id'])))
			if sectionForm.is_valid():
				section = sectionForm.save()
				return HttpResponse(simplejson.dumps({"status": "ok"}))
		else:
			sectionForm = SectionForm(request.POST)
			if sectionForm.is_valid():
				s = sectionForm.save(commit=False)
				s.creation_date = datetime.now()
				s.summary = su
				ss = Section.objects.filter(summary=su)
				if (len(ss) > 0):
					print ss.aggregate(Max("index"))
					s.index = ss.aggregate(Max("index"))['index__max'] + 1
				else:
					s.index = 0
				s.save()
				return HttpResponse(simplejson.dumps({"status": "ok", "id": s.id, "index": s.index}))
	raise Http404

def login(request):
	return render_to_response('main/login.html', {"loginForm": AuthenticationForm(request)})

def deletecomment(request, hash, id):
	ds = Document.objects.filter(hash=hash)
	if (len(ds) == 0):
		raise Http404
	d = ds[0]
	c = Comment.objects.get(pk=id)
	if (c.document.id != d.id):
		raise HttpResponse(simplejson.dumps({"status": "error", "message": "Comment doesn't belong to document"}))
	c.deleted = True
	c.save()
	return HttpResponse(simplejson.dumps({"status": "ok"}));

class SummaryForm(forms.ModelForm):
	class Meta:
		model = Summary
		fields = ('name',)

class SectionForm(forms.ModelForm):
	class Meta:
		model = Section
		fields = ('name', 'section')

class CommentForm(forms.ModelForm):
	class Meta:
		model = Comment
		fields = ('nickname', 'comment')

class DocumentUploadForm(forms.ModelForm):
	class Meta:
		model = Document
		fields = ('file', 'public')

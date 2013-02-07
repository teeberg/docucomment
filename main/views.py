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
	d = ds[0]

	# previous and next documents, for alphabetical navigation
	try:    previous = Document.objects.filter(name__lt=d.name, public=1).order_by('-name')[0]
	except: previous = None

	try:    next     = Document.objects.filter(name__gt=d.name, public=1).order_by('name')[0]
	except: next     = None

	if "nickname" in request.COOKIES:
		initial["nickname"] = request.COOKIES["nickname"]
	form = CommentForm(initial=initial)
	return render_to_response('main/document.html', {"document": d, 'commentForm': form, 'page': page, 'previous': previous, 'next': next})

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
	return JsonResponse(cs)

def renamedocument(request, hash):
	ret = {'status': 1}
	ds = Document.objects.filter(hash=hash)
	if len(ds) == 0:
		ret['message'] = 'No document exists with this hash.'
	elif 'name' not in request.POST:
		ret['message'] = 'No new name supplied.'
	else:
		d = ds[0]
		try:
			d.name = request.POST['name']
			d.save()
			ret['status'] = 0
			ret['name_escaped'] = escape(d.name)
		except Exception as ex:
			ret['message'] = 'An exception was thrown. Please notify an administrator.'
			traceback.print_exc(file=sys.stdout)
	return JsonResponse(ret)

def setnickname(request):
	response = {}
	if 'name' in request.POST:
		nickname = strip_tags(request.POST['name'])
		response['status'] = 0
		response['safenick'] = nickname
		http = JsonResponse(response)
		http.set_cookie("nickname", nickname)
		return http
	else:
		response['status'] = 1
		response['message'] = 'No new nick provided.'
		return JsonResponse(response)

def comment(request, hash, page):
	if request.method == 'POST':
		try:
			page = int(page)
		except:
			return JsonResponse({"status": 1, "message": "Non-numeric page supplied"})
		else:
			if page < 1:
				return JsonResponse({"status": 1, "message": "Invalid page supplied: Must lie inside the PDF's boundaries"})

		post = request.POST.copy()
		post.update({'nickname': strip_tags(request.POST['nickname'])})
		ds = Document.objects.filter(hash=hash)
		if len(ds) == 0:
			return JsonResponse({"status": 1, "message": "There is no document with this hash."})
		d = ds[0]
		if post.has_key('id') and len(post['id']) > 0:
			instance = Comment.objects.get(pk=int(post['id']))
			if instance == None:
				return JsonResponse({"status": 1, "message": "Trying to update non-existing comment."})
			elif instance.deleted == True:
				return JsonResponse({"status": 1, "message": "This comment has been deleted."})

			commentForm = CommentForm(post, instance=instance)
			if (commentForm.is_valid()):
				commentForm.save()
				return JsonResponse({"status": 0})
		else:
			commentForm = CommentForm(post)
			if commentForm.is_valid():
				c = commentForm.save(commit=False)
				c.creation_date = datetime.now()
				c.document = d
				c.page = page
				c.save()
				response = JsonResponse({"status": 0, "safenick": c.nickname})
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
			return JsonResponse({"status": "error", "message": "summary id doesn't correspond"})
		if "id" in request.POST and len(request.POST['id']) > 0:
			sectionForm = SectionForm(request.POST, instance=Section.objects.get(pk=int(request.POST['id'])))
			if sectionForm.is_valid():
				section = sectionForm.save()
				return JsonResponse({"status": "ok"})
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
				return JsonResponse({"status": "ok", "id": s.id, "index": s.index})
	raise Http404

def login(request):
	return render_to_response('main/login.html', {"loginForm": AuthenticationForm(request)})

def deletecomment(request, hash, id):
	ds = Document.objects.filter(hash=hash)
	ret = {"status": 0}
	if len(ds) == 0:
		ret.update(status=1, message="No document with this ID exists")
	else:
		d = ds[0]
		c = Comment.objects.get(pk=id)
		if c == None:
			ret.update(status=1, message="No comment with this ID exists")
		else:
			if c.document.id != d.id:
				ret.update(status=1, message="Comment does not belong to the provided document")
			else:
				c.deleted = True
				c.save()
	return JsonResponse(ret)

class JsonResponse(HttpResponse):
	def __init__(self, data, *args, **kwargs):
		if 'content_type' not in kwargs:
			kwargs.update(content_type='application/json')
		super(JsonResponse, self).__init__(simplejson.dumps(data), *args, **kwargs)

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

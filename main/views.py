from django import forms
from django.contrib import auth, messages
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.servers.basehttp import FileWrapper
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Max
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render, render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.utils.html import escape, strip_tags
from main.models import Space, Document, Comment, Summary, Section
from datetime import datetime, timedelta
from hashlib import sha1
from mimetypes import guess_type
import shutil
import sys
import traceback
import pprint

# Create your views here.

def home(request):
	if request.method == 'POST':
		if request.POST['action'] == 'create-space':
			spaceForm = SpaceForm(request.POST)
			if spaceForm.is_valid():
				ss = Space.objects.filter(name=request.POST["name"])
				if ss:
					space = ss[0]
				else:
					space = spaceForm.save(commit=False)
					space.creation_date = datetime.now()
					space.save()
				return redirect("/space/" + space.name)
	return render_to_response('main/home.html', {"view": "home", "spaceForm": SpaceForm()})
	
def space(request, space):
	ss = Space.objects.filter(name=space)
	if not ss:
		raise Http404
	s = ss[0]
	if request.method == 'POST':
		if request.POST['action'] == "post-document":
			uploadForm = DocumentUploadForm(request.POST, request.FILES)
			if uploadForm.is_valid() and request.FILES["file"].name.endswith(".pdf"):
				f = uploadForm.files["file"]
				hash = sha1("blob " + str(f.size) + "\0" + f.read()).hexdigest()
				ds = Document.objects.filter(space=s, hash=hash)
				if len(ds) == 0:
					d = uploadForm.save(commit=False)
					d.name = d.file.name
					d.hash = hash
					d.upload_date = datetime.now()
					d.space = s
					d.save()
				return redirect("/space/" + s.name + "/document/" + hash)
		elif request.POST['action'] == "post-summary":
			summaryForm = SummaryForm(request.POST)
			if summaryForm.is_valid():
				su = summaryForm.save(commit=False)
				su.creation_date = datetime.now()
				su.space = s
				su.save()
				return redirect("/space/" + s.name + "/summary/" + str(su.id))

	uploadForm = DocumentUploadForm()
	summaryForm = SummaryForm()
	
	return render_to_response('main/space.html', {"view": "space", "space": s, "documents": Document.objects.order_by('name').filter(space=s), "uploadForm": uploadForm, "summaries": Summary.objects.order_by('name').filter(space=s), "summaryForm": summaryForm})

def send_file(request, space, hash):
	ss = Space.objects.filter(name=space)
	if not ss:
		raise Http404
	s = ss[0]
	ds = Document.objects.filter(space=s, hash=hash)
	if len(ds) == 0:
		raise Http404
	d = ds[0]
	wrapper = FileWrapper(d.file)
	response = HttpResponse(wrapper, content_type=guess_type(d.name)[0])
	response['Content-Length'] = d.file.size
	response['Content-Disposition'] = "attachment; filename=\"{}\"".format(d.name)
	return response

def summary(request, space, id):
	ss = Space.objects.filter(name=space)
	if not ss:
		raise Http404
	s = ss[0]
	try:
		su = Summary.objects.get(pk=id)
	except ObjectDoesNotExist:
		raise Http404
	if su == None:
		raise Http404
	sectionForm = SectionForm()
	documents = Document.objects.filter(deleted=False, public=True).order_by("name")
	return render_to_response('main/summary.html', {"view": "summary", "space": s, "summary": su, "sectionForm": sectionForm, "documents": documents})

def document(request, space, hash):
	ss = Space.objects.filter(name=space)
	if not ss:
		raise Http404
	s = ss[0]
	ds = Document.objects.filter(space=s, hash=hash)
	if not ds:
		raise Http404
	try:
		page = int(request.GET['page']) if 'page' in request.GET else 1
	except:
		return redirect("/space/" + space + "/document/" + hash)
	initial = {}
	d = ds[0]

	# previous and next documents, for alphabetical navigation
	try:    previous = Document.objects.filter(space=space, name__lt=d.name, public=1).order_by('-name')[0]
	except: previous = None

	try:    next     = Document.objects.filter(space=space, name__gt=d.name, public=1).order_by('name')[0]
	except: next     = None

	if "nickname" in request.COOKIES:
		initial.update(nickname=request.COOKIES['nickname'])
	form = CommentForm(initial=initial)
	return render_to_response('main/document.html', {"view": "document", "space": s, "document": d, 'commentForm': form, 'page': page, 'previous': previous, 'next': next})

def sections(request, space, summary):
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

def comments(request, space, hash=None, page=None):
	if hash == None:
		comments = Comment.objects.filter(deleted=False).order_by('-creation_date')
	else:
		ds = Document.objects.filter(hash=hash)
		if not ds:
			raise Http404
		d = ds[0]
		comments = Comment.objects.filter(document=d, page=page, deleted=False)
	cs = []
	for comment in comments:
		c = {"id": comment.id, "nickname": escape(comment.nickname), "nickname_plain": comment.nickname, "comment": comment.comment_parsed(), "comment_plain": comment.comment, "page": comment.page, "document_public": comment.document.public}
		cs.append(c)
		if comment.document.public:
			c.update(document_hash=comment.document.hash)
	return JsonResponse(cs)

def renamedocument(request, space, hash):
	ret = {'status': 1}
	ds = Document.objects.filter(hash=hash)
	if not ds:
		ret.update(message='No document exists with this hash.')
	elif 'name' not in request.POST:
		ret.update(message='No new name supplied.')
	else:
		d = ds[0]
		try:
			d.name = request.POST['name']
			d.save()
			ret.update(status=0, name_escaped = escape(d.name))
		except Exception as ex:
			ret.update(message='An exception was thrown. Please notify an administrator.')
			traceback.print_exc(file=sys.stdout)
	return JsonResponse(ret)

def setnickname(request):
	response = {}
	if 'name' in request.POST:
		nickname = strip_tags(request.POST['name'])
		response.update(status=0, safenick=nickname)
		http = JsonResponse(response)
		http.set_cookie("nickname", nickname)
		return http
	else:
		response.update(status=1, message='No new nick provided.')
		return JsonResponse(response)

def comment(request, space, hash, page):
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
		if not ds:
			return JsonResponse({"status": 1, "message": "There is no document with this hash."})
		d = ds[0]
		if post.has_key('id') and len(post['id']) > 0:
			instance = Comment.objects.get(pk=int(post['id']))
			if instance == None:
				return JsonResponse({"status": 1, "message": "Trying to update non-existing comment."})
			elif instance.deleted == True:
				return JsonResponse({"status": 1, "message": "This comment has been deleted."})

			commentForm = CommentForm(post, instance=instance)
			if commentForm.is_valid():
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

def section(request, space, summary):
	try:
		su = Summary.objects.get(pk=summary)
	except ObjectDoesNotExist:
		raise Http404
	if su == None:
		raise Http404
	if request.method == "POST":
		if request.POST["summary_id"] != summary:
			return JsonResponse({"status": 1, "message": "summary id doesn't correspond"})
		if "id" in request.POST and len(request.POST['id']) > 0:
			sectionForm = SectionForm(request.POST, instance=Section.objects.get(pk=int(request.POST['id'])))
			if sectionForm.is_valid():
				section = sectionForm.save()
				return JsonResponse({"status": 0})
		else:
			sectionForm = SectionForm(request.POST)
			if sectionForm.is_valid():
				s = sectionForm.save(commit=False)
				s.creation_date = datetime.now()
				s.summary = su
				ss = Section.objects.filter(summary=su)
				if len(ss) > 0:
					s.index = ss.aggregate(Max("index"))['index__max'] + 1
				else:
					s.index = 0
				s.save()
				return JsonResponse({"status": 0, "id": s.id, "index": s.index})
	raise Http404

def login(request):
	args = {}
	if not request.user.is_authenticated() and request.POST:
		form = AuthenticationForm(request=request, data=request.POST)
		args.update(form=form)

		# the formular validation will check if this cookie is set
		request.session.set_test_cookie()

		if form.is_valid():
			auth.login(request, form.get_user())
			messages.success(request, 'You are now logged in.')
			return redirect('/')
	else:
		args.update(form=AuthenticationForm())

	return render(request, 'main/login.html', args)

def logout(request):
	auth.logout(request)
	messages.success(request, 'You have been logged out.')
	return redirect('/')

def register(request):
	args = {}
	if request.user.is_authenticated():
		return redirect('/')
	elif not request.user.is_authenticated() and request.POST:
		form = UserCreationForm(request.POST)
		args.update(form=form)
		if form.is_valid():
			user = form.save()
			messages.success(request, 'Your account has been created!')
			return redirect('/login')
	elif not request.POST:
		args.update(form=UserCreationForm())
	else:
		return redirect('/')
	
	return render(request, 'main/register.html', args)

def deletecomment(request, space, hash, id):
	ds = Document.objects.filter(hash=hash)
	ret = {"status": 0}
	if len(ds) == 0:
		ret.update(status=1, message="No document with this ID exists")
	else:
		d = ds[0]
		c = Comment.objects.get(pk=id)
		if c == None:
			ret.update(status=1, message="No comment with this ID exists")
		elif c.document.id != d.id:
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

class SpaceForm(forms.ModelForm):
	class Meta:
		model = Space
		fields = ('name',)

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

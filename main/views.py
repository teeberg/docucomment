from django import forms
from django.http import Http404, HttpResponse
from django.core.servers.basehttp import FileWrapper
from django.utils import simplejson
from django.utils.html import escape, strip_tags
from django.shortcuts import render_to_response, redirect
from django.contrib.auth.forms import AuthenticationForm
from main.models import Document, Comment
from datetime import datetime, timedelta
from hashlib import sha1
from mimetypes import guess_type
import sys
import traceback

# Create your views here.

def home(request):
	if request.method == 'POST':
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
	else:
		uploadForm = DocumentUploadForm()
	
	return render_to_response('main/home.html', {"page": "home", "documents": Document.objects.order_by('name').all(), "uploadForm": uploadForm})

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

def setnickname(request):
	response = {}
	if 'name' in request.POST:
		nickname = strip_tags(request.POST['name'])
		response['status'] = 0
		response['safenick'] = nickname
		http = HttpResponse(simplejson.dumps(response))
		http.set_cookie("nickname", nickname)
		return http
	else:
		response['status'] = 1
		response['message'] = 'No new nick provided.'
		return HttpResponse(simplejson.dumps(response))

def comment(request, hash, page):
	if request.method == 'POST':
		post = request.POST.copy()
		post.update({'nickname': strip_tags(request.POST['nickname'])})
		d = Document.objects.get(hash=hash)
		if d == None:
			return HttpResponse(simplejson.dumps({"status": 1, "message": "There is no document with this hash."}))
		if post.has_key('id') and len(post['id']) > 0:
			commentForm = CommentForm(post, instance=Comment.objects.get(pk=int(post['id'])))
			if (commentForm.is_valid()):
				commentForm.save()
				return HttpResponse(simplejson.dumps({"status": 0}));
		else:
			commentForm = CommentForm(post)
			if (commentForm.is_valid()):
				c = commentForm.save(commit=False)
				c.creation_date = datetime.now()
				c.document = d
				c.page = page
				c.save()
				response = HttpResponse(simplejson.dumps({"status": 0, "safenick": c.nickname}))
				response.set_cookie("nickname", c.nickname)
				return response
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

class CommentForm(forms.ModelForm):
	class Meta:
		model = Comment
		fields = ('nickname', 'comment')

class DocumentUploadForm(forms.ModelForm):
	class Meta:
		model = Document
		fields = ('file', 'public')

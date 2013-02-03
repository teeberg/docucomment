from django import forms
from django.http import Http404, HttpResponse
from django.core.servers.basehttp import FileWrapper
from django.utils import simplejson
from django.utils.html import escape, strip_tags
from django.shortcuts import render_to_response, redirect
from django.contrib.auth.forms import AuthenticationForm
from main.models import Document, Comment
from datetime import datetime
from hashlib import sha1
from mimetypes import guess_type

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
	
	comments = Comment.objects.order_by('-creation_date').filter(deleted=False)
	for c in comments:
		c.comment = c.comment_parsed()
	return render_to_response('main/home.html', {"documents": Document.objects.order_by('name').all(), "uploadForm": uploadForm, "comments": comments})

def send_file(request, hash):
	ds = Document.objects.filter(hash=hash)
	if (len(ds) == 0):
		raise Http404
	d = ds[0]
	wrapper = FileWrapper(d.file)
	response = HttpResponse(wrapper, content_type=guess_type(d.name)[0])
	response['Content-Length'] = d.file.size
	response['Content-Disposition'] = "attachment; filename=\"%s\"" % d.name
	return response

def document(request, hash):
	ds = Document.objects.filter(hash=hash)
	if (len(ds) == 0):
		raise Http404
	try:
		page = int(request.GET['page']) if 'page' in request.GET else 1
	except:
		return redirect("/document/"+hash)
	return render_to_response('main/document.html', {"document": ds[0], 'commentForm': CommentForm(), 'page': page})

def comments(request, hash, page):
	ds = Document.objects.filter(hash=hash)
	if (len(ds) == 0):
		raise Http404
	d = ds[0]
	comments = Comment.objects.filter(document=d, page=page, deleted=False)
	cs = []
	for comment in comments:
		c = {"id": comment.id, "nickname": escape(comment.nickname), "nickname_plain": comment.nickname, "comment": comment.comment_parsed(), "comment_plain": comment.comment}
		cs.append(c)
	return HttpResponse(simplejson.dumps(cs))

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
			if (commentForm.is_valid()):
				commentForm.save()
				return HttpResponse(simplejson.dumps({"status": "ok"}));
		else:
			commentForm = CommentForm(post)
			if (commentForm.is_valid()):
				c = commentForm.save(commit=False)
				c.creation_date = datetime.now()
				c.document = d
				c.page = page
				c.save()
				return HttpResponse(simplejson.dumps({"status": "ok"}));
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

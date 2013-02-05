from django.conf.urls import patterns, include, url

urlpatterns = patterns('main.views',
	url(r'^$', 'home'),
	url(r'^login?$', 'login'),
	url(r'^document/(?P<hash>\w+)/deletecomment/(?P<id>\d+)$', 'deletecomment'),
	url(r'^document/(?P<hash>\w+)$', 'document'),
	url(r'^document/(?P<hash>\w+)/file$', 'send_file'),
	url(r'^document/(?P<hash>\w+)/page/(?P<page>\d+)/comments$', 'comments'),
	url(r'^document/(?P<hash>\w+)/page/(?P<page>\d+)/comment$', 'comment'),
	url(r'^document/(?P<hash>\w+)/rename$', 'renamedocument'),
)

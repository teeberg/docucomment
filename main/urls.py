from django.conf.urls import patterns, include, url

urlpatterns = patterns('main.views',
	url(r'^$', 'home'),
	url(r'^login?$', 'login'),
	url(r'^setnickname$', 'setnickname'),
	url(r'^space/(?P<space>\w+)$', 'space'),
	url(r'^space/(?P<space>\w+)/comments$', 'comments'),
	url(r'^space/(?P<space>\w+)/summary/(?P<id>\d+)$', 'summary'),
	url(r'^space/(?P<space>\w+)/summary/(?P<summary>\d+)/section$', 'section'),
	url(r'^space/(?P<space>\w+)/summary/(?P<summary>\d+)/sections$', 'sections'),
	url(r'^space/(?P<space>\w+)/document/(?P<hash>\w+)/deletecomment/(?P<id>\d+)$', 'deletecomment'),
	url(r'^space/(?P<space>\w+)/document/(?P<hash>\w+)$', 'document'),
	url(r'^space/(?P<space>\w+)/document/(?P<hash>\w+)/file$', 'send_file'),
	url(r'^space/(?P<space>\w+)/document/(?P<hash>\w+)/page/(?P<page>\d+)/comments$', 'comments'),
	url(r'^space/(?P<space>\w+)/document/(?P<hash>\w+)/page/(?P<page>\d+)/comment$', 'comment'),
	url(r'^space/(?P<space>\w+)/document/(?P<hash>\w+)/rename$', 'renamedocument'),
)

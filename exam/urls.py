from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('exam.views',
    url(r'^$', 'index'),
    url(r'^start/$', 'start'),
    url(r'^quit/$', 'quit'),
    url(r'^complete/$', 'complete'),
    url(r'^monitor/$', 'monitor'),
    url(r'^(?P<q_id>\d+)/$', 'question'),
    url(r'^(?P<q_id>\d+)/check/$', 'check'),
)

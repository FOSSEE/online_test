from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('exam.views',
    url(r'^$', 'index'),
    url(r'^login/$', 'user_login'),
    url(r'^register/$', 'user_register'),
    url(r'^start/$', 'start'),
    url(r'^quit/$', 'quit'),
    url(r'^complete/$', 'complete'),
    url(r'^monitor/$', 'monitor'),
    url(r'^monitor/(?P<quiz_id>\d+)/$', 'monitor'),    
    url(r'^user_data/(?P<username>[a-zA-Z0-9_.]+)/$', 'user_data'),
    url(r'^grade_user/(?P<username>[a-zA-Z0-9_.]+)/$', 'grade_user'),
    url(r'^(?P<q_id>\d+)/$', 'question'),
    url(r'^(?P<q_id>\d+)/check/$', 'check'),
)

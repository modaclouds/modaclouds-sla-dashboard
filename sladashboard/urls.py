from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'sla.views.home', name='home'),
    url(r'^slagui/', include('slagui.urls')),

    url(r'^admin/', include(admin.site.urls)),
)

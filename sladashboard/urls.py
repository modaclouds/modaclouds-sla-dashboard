from django.conf.urls import patterns, include, url

from django.contrib import admin
from slagui import views

admin.autodiscover()


urlpatterns = patterns('',
    # Examples:
    url(r'^$', views.agreements_summary),
    url(r'^slagui/', include('slagui.urls')),

    url(r'^admin/', include(admin.site.urls)),
)

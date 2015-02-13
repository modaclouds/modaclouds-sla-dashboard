from django.conf.urls import patterns, url

from slagui import views

urlpatterns = patterns(
    '',

    # eg: /$slaroot/
    #url(r'^$', views.index, name='index'),
    #url(r'^(?P<is_provider>provider/)?agreements[/]$',
    #    views.agreements_summary, name='agreements_summary'),
    url(
        r'^agreements[/]$',
        views.agreements_summary,
        kwargs={'consumer_id': None, 'provider_id': None},
        name='agreements_summary'
    ),
    url(
        r'^consumer/(?P<consumer_id>.+)/agreements[/]$',
        views.agreements_summary,
        kwargs={'provider_id': None},
        name='consumer_agreements_summary'
    ),
    url(
        r'^provider/(?P<provider_id>.+)/agreements[/]$',
        views.agreements_summary,
        kwargs={'consumer_id': None},
        name='provider_agreements_summary'
    ),
    url(
        r'^agreements/(?P<agreement_id>[\w-]+)$',
        views.agreements_summary,
        name='agreement'
    ),
    url(
        r'^agreements/(?P<agreement_id>[\w-]+)/guarantees/(?P<guarantee_name>[\w-]+)/violations$',
        views.agreement_term_violations,
        name='agreement_term_violations'
    ),
    #url(r'^agreements/(?P<agreement_id>\w+)/violations$',
    #    views.agreement_violations, name='agreement_violations'),
    url(
        r'^agreements/(?P<agreement_id>[\w-]+)/detail$',
        views.agreement_details,
        name='agreement_details'
    ),
    url(
        r'^raw/agreements/(?P<agreement_id>[\w-]+)',
        views.raw_agreement,
        name='raw_agreement'
    ),
    url(
        r'^raw/templates/(?P<template_id>[\w-]+)',
        views.raw_template,
        name='raw_template'
    ),

    #url(r'^consumer/(?P<consumer_id>\w+)$', views.consumer_agreements, name='consumer_agreements'),

    #url(r'^/?$', views.home, name='home'),
    #url(r'^administration/?$', views.admin, name='admin'),
    #url(r'^catalogue/?$', 'views.catalogue', name='catalogue'),
)

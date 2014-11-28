
from django.shortcuts import render
from django.conf import settings
from django.core.urlresolvers import reverse
from django import forms

from slaclient import restclient
from slaclient import wsag_model

import wsag_helper

VIOLATED = wsag_model.AgreementStatus.StatusEnum.VIOLATED
NON_DETERMINED = wsag_model.AgreementStatus.StatusEnum.NON_DETERMINED
FULFILLED = wsag_model.AgreementStatus.StatusEnum.FULFILLED

#
# This is not thread safe and there may be problems if SLA_MANAGER_URL is not
# a fixed value
#
# See:
# http://blog.roseman.org.uk/2010/02/01/middleware-post-processing-django-gotcha
#
factory = restclient.Factory(settings.SLA_MANAGER_URL)


class Rol(object):
    CONSUMER = "CONSUMER"
    PROVIDER = "PROVIDER"
    ADMIN = "ADMIN"


class FilterForm(forms.Form):
    _attrs = {'class': 'form-control'}
    exclude = ()
    status = forms.ChoiceField(
        choices=[
            ('', 'All'),
            (wsag_model.AgreementStatus.StatusEnum.FULFILLED, 'Fulfilled'),
            (wsag_model.AgreementStatus.StatusEnum.VIOLATED, 'Violated'),
            (wsag_model.AgreementStatus.StatusEnum.NON_DETERMINED,
                'Non determined')],
        widget=forms.Select(attrs=_attrs),
        required=False
    )
    provider = forms.CharField(
        widget=forms.TextInput(attrs=_attrs),
        required=False
    )
    consumer = forms.CharField(
        widget=forms.TextInput(attrs=_attrs),
        required=False
    )


class AgreementsFilter(object):
    def __init__(self, status=None, provider=None, consumer=None):
        self.status = status
        self.provider = provider
        self.consumer = consumer

    def __repr__(self):
        return "<AgreementsFilter(status={}, provider={}, consumer={})>".format(
            self.status, self.provider, self.consumer
        )

    @staticmethod
    def _check(expectedvalue, actualvalue):
        if expectedvalue is None or expectedvalue == '':
            return True
        else:
            return actualvalue == expectedvalue

    def check(self, agreement):
        """Check if this agreement satisfy the filter.

        The agreement must be previously annotated
        """
        guaranteestatus = agreement.guaranteestatus
        provider = agreement.context.provider
        consumer = agreement.context.consumer
        return (
            AgreementsFilter._check(self.status, guaranteestatus) and
            AgreementsFilter._check(self.provider, provider) and
            AgreementsFilter._check(self.consumer, consumer)
        )


class ContactForm(forms.Form):
    subject = forms.CharField(max_length=100)
    message = forms.CharField()
    sender = forms.EmailField()
    cc_myself = forms.BooleanField(required=False)


#
#
# Right now, the user handling is hard-wired.
# When entering /agreements, session.rol is set to "CONSUMER"
# When entering /provider/agreements session.rol is set to "PROVIDER"
#
# The providerId or consumerId are hardwired in _get_consumer_id() and
#   _get_provider_id()
#
# session.rol is retrieved in the rest of views.
#
#
def index(request):
    context = {'now': 'i am in index'}
    return render(request, 'index.html', context)


def home(request):
    context = {
    }
    return render(request, 'index.html', context)


def admin(request):
    if False:  # request.user.is_staff:
        context = {
        }
        return render(request, 'admin/admin.html', context)
    else:
        #build_response(request, 403, 'Forbidden')
        pass


def agreements_summary(request, provider_id=None, consumer_id=None):
    """
    :param django.http.HttpRequest request:
    :param bool is_provider:
    """
    agreement_id = None
    if provider_id is None and consumer_id is None:
        rol = Rol.ADMIN
    else:
        rol = Rol.PROVIDER if provider_id is not None else Rol.CONSUMER
    #
    # Save rol in session
    #
    request.session["rol"] = rol

    filter_ = None
    form = FilterForm(request.GET)
    if form.is_valid():
        filter_ = _get_filter_from_form(form)
    if filter_ is None:
        form = FilterForm()

    if rol == Rol.PROVIDER:
        user_id = provider_id
        agreements = _get_agreements(
            agreement_id, provider_id=provider_id, filter_=filter_)
        form.exclude = ('provider',)
    elif rol in (Rol.CONSUMER, Rol.ADMIN):
        user_id = consumer_id
        agreements = _get_agreements(
            agreement_id, consumer_id=consumer_id, filter_=filter_)
        form.exclude = ('consumer',)
    else:
        raise ValueError("rol '{}' not supported".format(rol))

    context = {
        'rol': rol,
        'user_id': user_id,
        'agreements': agreements,
        'form': form,
    }
    return render(request, 'slagui/agreements.html', context)


def agreement_details(request, agreement_id):
    annotator = wsag_helper.AgreementAnnotator()
    agreement = _get_agreement(agreement_id)
    violations = _get_agreement_violations(agreement_id)
    status = _get_agreement_status(agreement_id)
    ejob = _get_enforcementjob(agreement_id)
    annotator.annotate_agreement(agreement, status, violations, ejob)

    if not ejob.enabled:
        status_str = wsag_model.AgreementStatus.StatusEnum.NON_DETERMINED
    elif status.guaranteestatus != VIOLATED:
        status_str = FULFILLED
    else:
        status_str = VIOLATED

    violations_by_date = wsag_helper.get_violations_bydate(violations)
    # should be obtained from rest client
    agreement_resourceurl = "{}/agreements/{}".format(settings.SLA_MANAGER_URL, agreement_id)
    template_id = agreement.context.template_id
    template_resourceurl = "{}/templates/{}".format(settings.SLA_MANAGER_URL, template_id)
    context = {
        'backurl': _get_backurl(request),
        'agreement_id': agreement_id,
        'agreement': agreement,
        'status': status_str,
        'violations_by_date': violations_by_date,
        'resource': agreement_resourceurl,
        'template_resource': template_resourceurl,
    }
    return render(request, 'slagui/agreement_detail.html', context)


def agreement_term_violations(request, agreement_id, guarantee_name):

    annotator = wsag_helper.AgreementAnnotator()
    agreement = _get_agreement(agreement_id)
    violations = _get_agreement_violations(agreement_id, guarantee_name)
    annotator.annotate_agreement(agreement)
    context = {
        'backurl': _get_backurl(request),
        'agreement_id': agreement_id,
        'guarantee_term': agreement.guaranteeterms[guarantee_name],
        'violations': violations,
        'agreement': agreement,
    }
    return render(request, 'slagui/violations.html', context)


def _get_agreements_client():
    return factory.agreements()


def _get_violations_client():
    return factory.violations()


def _get_enforcementjobs_client():
    return factory.enforcements()


def _get_rol(request):
    return request.session.get("rol", Rol.CONSUMER)


def _get_backurl(request):
    rol = _get_rol(request)

    if rol == Rol.ADMIN:
        backurl = reverse(
            'agreements_summary',
            kwargs=dict(provider_id=None, consumer_id=None)
        )
    #elif rol == Rol.PROVIDER:
    #    backurl = reverse(
    #        'provider_agreements_summary',
    #        kwargs=dict(provider_id=None, consumer_id=None)
    #    )
    #elif rol == Rol.CONSUMER:
    #    backurl = reverse(
    #        'consumer_agreements_summary',
    #        kwargs=dict(provider_id=None, consumer_id=None)
    #    )
    else:
        raise ValueError("Rol '{}' not support".format(rol))
    return backurl


def _get_agreement(agreement_id):
    """

    :rtype : wsag_model.Agreement
    """
    agreements_client = _get_agreements_client()
    agreement, response = agreements_client.getbyid(agreement_id)
    return agreement


def _get_filter_from_form(form):
    data = form.cleaned_data
    result = AgreementsFilter(
        data["status"], data["provider"], data["consumer"])
    print result
    return result


def _get_agreements(agreement_id, provider_id=None, consumer_id=None,
                    filter_=None):
    """Get agreements

    :rtype : list[wsag_model.Agreement]
    :param str agreement_id:
    :param str provider_id:
    :param str consumer_id:
    :param dict[str,str] filter_:
    """
    agreements_client = _get_agreements_client()
    if agreement_id is None:
        if consumer_id is not None:
            agreements, response = agreements_client.getbyconsumer(consumer_id)
        elif provider_id is not None:
            agreements, response = agreements_client.getbyprovider(provider_id)
        else:
            agreements, response = agreements_client.getall()
    else:
        agreement, response = agreements_client.getbyid(agreement_id)
        agreements = [agreement]

    annotator = wsag_helper.AgreementAnnotator()
    for agreement in agreements:
        id_ = agreement.agreement_id
        status = _get_agreement_status(id_)
        ejob = _get_enforcementjob(id_)
        annotator.annotate_agreement(agreement, status=status, ejob=ejob)

    if filter_ is not None:
        print "FILTERING ", repr(filter_)
        agreements = filter(filter_.check, agreements)
    else:
        print "NOT FILTERING"
    return agreements


def _get_agreements_by_consumer(consumer_id):
    """

    :rtype : list[wsag_model.Agreement]
    """
    agreements_client = _get_agreements_client()
    agreements, response = agreements_client.getbyconsumer(consumer_id)
    return agreements


def _get_agreement_status(agreement_id):
    """

    :rtype : wsag_model.AgreementStatus
    """
    agreements_client = _get_agreements_client()
    status, response = agreements_client.getstatus(agreement_id)
    return status


def _get_agreement_violations(agreement_id, term=None):
    """

    :rtype : list[wsag_model.Violation]
    """
    violations_client = _get_violations_client()
    violations, response = violations_client.getbyagreement(agreement_id, term)
    return violations


def _get_enforcementjob(agreement_id):
    """

    :rtype : wsag_model.EnforcementJob
    """
    ejobs_client = _get_enforcementjobs_client()
    status, response = ejobs_client.getbyid(agreement_id)
    return status

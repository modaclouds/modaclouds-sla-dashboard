from slaclient import wsag_model
from slaclient.wsag_model import AgreementStatus
from slaclient.wsag_model import Violation


VIOLATED = AgreementStatus.StatusEnum.VIOLATED
NON_DETERMINED = AgreementStatus.StatusEnum.NON_DETERMINED
FULFILLED = AgreementStatus.StatusEnum.FULFILLED


def get_violations_bydate(violations):
    """Returns a list of violations per date, from a list of violations

    :param violations list[Violation]:
    :rtype: list
    """
    d = dict()
    for v in violations:
        assert isinstance(v, Violation)
        date = v.datetime.date()
        if not date in d:
            d[date] = []
        d[date].append(v)

    result = [(key, d[key]) for key in sorted(d.keys(), reverse=True)]
    return result


class AgreementAnnotator(object):
    """Annotates an agreement with the following attributes:

    agreement.guaranteestatus
    agreement.statusclass
    agreement.guaranteeterms[*].status
    agreement.guaranteeterms[*].statusclass
    agreement.guaranteeterms[*].nviolations
    agreement.guaranteeterms[*].servicelevelobjetive.bounds

    """
    def __init__(self):
        pass

    @staticmethod
    def _get_statusclass(status, enabled):
        if not enabled:
            return "non-determined"
        return "success" if status in (FULFILLED, NON_DETERMINED) else "error"

    def _annotate_guaranteeterm(self, term, violations):
        #
        # Annotate a guarantee term: set bounds and violations
        #
        level = term.servicelevelobjective.customservicelevel
        bounds = [level.minvalue, level.maxvalue, '[', ']']
        term.servicelevelobjective.bounds = bounds

        #
        # set status attribute if not set before
        #
        if not hasattr(term, 'status'):
            term.status = wsag_model.AgreementStatus.StatusEnum.NON_DETERMINED
        #
        # TODO: efficiency
        #
        term_violations = [v for v in violations if v.belongs_to(term)]
        term.nviolations = len(term_violations)

    def _annotate_guaranteeterm_by_status(
            self, agreement, termstatus, violations, enabled):
        #
        # Annotate a guarantee term: it is different from the previous
        # one in that this takes the status into account.
        #
        name = termstatus.name
        status = termstatus.status

        term = agreement.guaranteeterms[name]
        term.status = status
        term.statusclass = AgreementAnnotator._get_statusclass(status, enabled)
        self._annotate_guaranteeterm(term, violations)

    def annotate_agreement(
            self, agreement, status=None, violations=(), ejob=None):

        """Annotate an agreement with certain values needed in the templates

        :param wsag_model.Agreement agreement: agreement to annotate
        :param wsag_model.AgreementStatus status: status of the agreement.
        :param violations: list of agreement's violations
            (wsag_model.Violation[])
        :param wsag_model.EnforcementJob ejob: EnformentJob of agreement
        """
        a = agreement
        enabled = ejob.enabled if ejob is not None else False
        if status is not None:
            a.guaranteestatus = status.guaranteestatus
            a.statusclass = self._get_statusclass(
                status.guaranteestatus, enabled)
            for termstatus in status.guaranteeterms:
                self._annotate_guaranteeterm_by_status(
                    agreement, termstatus, violations, enabled)
        else:
            a.guaranteestatus = NON_DETERMINED
            for termname, term in agreement.guaranteeterms.items():
                self._annotate_guaranteeterm(term, violations)

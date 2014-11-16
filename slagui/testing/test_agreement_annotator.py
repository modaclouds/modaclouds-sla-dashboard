from unittest import TestCase
import datetime
import uuid

from slagui.wsag_helper import AgreementAnnotator
from slaclient.wsag_model import Violation
from slaclient.wsag_model import AgreementStatus
from slaclient import xmlconverter


VIOLATED = AgreementStatus.StatusEnum.VIOLATED
NON_DETERMINED = AgreementStatus.StatusEnum.NON_DETERMINED
FULFILLED = AgreementStatus.StatusEnum.FULFILLED

class AgreementAnnotatorTestCase(TestCase):

    def setUp(self):
        conv = xmlconverter.AgreementConverter()
        self.agreement = xmlconverter.convertfile(
            conv, "slagui/testing/agreement.xml")
        """:type : Agreement"""

        self.status = self._new_agreementstatus(
            VIOLATED,
            [ ("GT_ResponseTime", FULFILLED),
              ("GT_Performance", VIOLATED) ]
        )

        self.emptystatus = self._new_agreementstatus(
            NON_DETERMINED,
            [ ("GT_ResponseTime", NON_DETERMINED),
              ("GT_Performance", NON_DETERMINED) ]
        )

        self.violations = [
            self._new_violation("Performance"),
            self._new_violation("Performance"),
            self._new_violation("Performance")
        ]

        self.checkviolations = {
            "GT_Performance": 3,
            "GT_ResponseTime": 0
        }

        self.emptycheckviolations = {
            "GT_Performance": 0,
            "GT_ResponseTime": 0
        }
        self.annotator = AgreementAnnotator()

    def _new_agreementstatus(self, guaranteestatus, terms):
        result = AgreementStatus()
        result.guaranteestatus = guaranteestatus
        for item in terms:
            result.guaranteeterms.append(
                self._new_termstatus(*item)
            )
        return result

    def _new_termstatus(self, name, status):
        tstatus = AgreementStatus.GuaranteeTermStatus()
        tstatus.name = name
        tstatus.status = status
        return tstatus

    def _new_violation(self, metric):
        v = Violation()
        v.actual_value = 0
        v.datetime = datetime.datetime.now()
        v.metric_name = metric
        v.uuid = uuid.uuid4()
        return v

    def _check(self, agreement, status, violations):
        """Checks annotation

        :param slagui.wsag_model.Agreement agreement:
        :param slagui.wsag_model.AgreementStatus status:
        :param dict[str,int] violations:
        """
        self.assertEquals(status.guaranteestatus, agreement.guaranteestatus)
        for term in status.guaranteeterms:
            self.assertEquals(
                term.status, agreement.guaranteeterms[term.name].status)
        for termname in violations.keys():
            self.assertEquals(
                violations[termname],
                agreement.guaranteeterms[termname].nviolations
            )

    def test_annotate_agreement1(self):
        self.annotator.annotate_agreement(self.agreement)
        self._check(self.agreement, self.emptystatus, self.emptycheckviolations)

    def test_annotate_agreement3(self):
        self.annotator.annotate_agreement(
            self.agreement, self.status)
        self._check(self.agreement, self.status, self.emptycheckviolations)

    def test_annotate_agreement5(self):
        self.annotator.annotate_agreement(
            self.agreement, self.status, self.violations)
        self._check(self.agreement, self.status, self.checkviolations)

    def test_parse_bounds_between(self):
        tests = [
            ("m BETWEEN (0, 1)",                    [0, 1, '[']),
            ("m BETWEEN 0, 1",                      [0, 1, '[']),
            ("m BETWEEN ",                          [None, None, '[']),
            ('{"constraint" : "m BETWEEN 0,1"}',    [0, 1, '[']),
        ]
        self._test_bounds(AgreementAnnotator._parse_bounds_between, tests)

    def test_parse_bounds_rest(self):
        tests = [
            ("m LT 1)",                     ["-INF", 1, '(']),
            ("m LE 1)",                     ["-INF", 1, '[']),
            ("m GE 0)",                     [0, "INF", '[']),
            ("m GT 0)",                     [0, "INF", '(']),
            ("m EQ 0)",                     [0, 0, '[']),
            ('{"constraint" : "m LT 1"}',   ["-INF", 1, '(']),
        ]
        self._test_bounds(AgreementAnnotator._parse_bounds_rest, tests)

    def _test_bounds(self, f, tests):
        for t in tests:
            slo = t[0]
            expected = t[1]
            current = f(slo)
            self.assertEquals(
                expected,
                current,
                "expected={} current={} slo={}".format(expected, current, slo)
            )


from . import common
from odoo.tests import tagged
from odoo.exceptions import RedirectWarning


@tagged("-at_install", "post_install")
class AccountJournalTest(common.L10nDOTestsCommon):
    def test_001_raise_redirect(self):
        """
        Checks Journal raises RedirectWarning if trying to
        setup fiscal journal without company vat
        """

        journal = self.env["account.journal"].search(
            [
                ("type", "=", "sale"),
                ("company_id", "=", self.do_company.id),
            ],
            limit=1,
        )

        with self.assertRaises(RedirectWarning):
            self.do_company.vat = False
            journal._get_journal_ncf_types()

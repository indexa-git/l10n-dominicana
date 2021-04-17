from odoo import tools
from odoo.tests.common import TransactionCase
from odoo.modules.module import get_module_resource


class AccountMoveTest(TransactionCase):
    def _load(self, module, *args):
        tools.convert_file(
            self.cr,
            "l10n_do_accounting",
            get_module_resource(module, *args),
            {},
            "init",
            False,
            "test",
            self.registry._assertion_report,
        )

    def setUp(self):
        super(AccountMoveTest, self).setUp()

        # Minimal accounting setup
        self._load("account", "test", "account_minimal_test.xml")

        country_do = self.env.ref("base.do").id

        # Company setup
        company = self.env.user.company_id
        company.write({"vat": "131793916", "country_id": country_do})

        # Accounting setup
        self.journal_obj = self.env["account.journal"]
        posted_invoices = self.env["account.move"].search([("type", "!=", "entry")])
        posted_invoices.button_draft()

        for journal in self.journal_obj.search([("type", "in", ("sale", "purchase"))]):
            journal.l10n_latam_use_documents = True

        # Fiscal partner
        self.partner = self.env["res.partner"].create(
            {
                "name": "Jimmy",
                "vat": "40229590076",
                "country_id": country_do,
                "l10n_do_dgii_tax_payer_type": "taxpayer",
            }
        )

        # Demo product
        self.product = self.env.ref("product.product_product_4")

    def create_invoice(self, invoice_type, document_number="", expense_type=""):
        inv = self.env["account.move"].create(
            {
                "type": invoice_type,
                "partner_id": self.partner.id,
                "l10n_latam_document_number": document_number,
                "l10n_do_expense_type": expense_type,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 1,
                            "price_unit": 110.0,
                        },
                    )
                ],
            }
        )
        inv.post()
        return inv

    def test_001_account_move_cancel(self):
        """
        Check fiscal invoices button cancel function returns an action dict
        """

        in_invoice = self.create_invoice("in_invoice", "B0100000001", "02")
        self.assertEqual(type(in_invoice.button_cancel()), type({}))

        out_invoice = self.create_invoice("out_invoice")
        self.assertEqual(type(out_invoice.button_cancel()), type({}))

    def test_002_account_move_cancel(self):
        """
        Check normal account move cancel function doesn't get any
        return value
        """

        journal = self.journal_obj.create(
            {"name": "Misc Journal", "type": "general", "code": "CACA"}
        )

        move = self.env["account.move"].create(
            {
                "journal_id": journal.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "2",
                            "debit": 0.0,
                            "credit": 100,
                            "account_id": self.env.ref("l10n_do_accounting.xfa").id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "2",
                            "debit": 100,
                            "credit": 0.0,
                            "account_id": self.env.ref("l10n_do_accounting.cas").id,
                        },
                    ),
                ],
            }
        )

        self.assertEqual(move.button_cancel(), None)

    def test_003_custom_refund_type(self):
        """
        Check Refunds using refund type feature are created correctly
        """

        # Customer Credit Notes
        out_invoice = self.create_invoice("out_invoice")
        refund_wizard = (
            self.env["account.move.reversal"]
            .with_context(active_ids=out_invoice.ids, active_model=out_invoice._name)
            .create({})
        )
        refund_wizard.write(
            {"refund_type": "percentage", "reason": "test", "percentage": 10}
        )
        result_invoice = self.env["account.move"].browse(
            refund_wizard.reverse_moves()["res_id"]
        )
        self.assertRecordValues(
            result_invoice.line_ids,
            [
                {"name": "test", "price_unit": 11},
                {"name": "", "price_unit": -11, "debit": 11, "credit": 0},
            ],
        )

        # Supplier Credit Notes
        in_invoice = self.create_invoice("in_invoice", "B0100000001", "02")
        refund_wizard = (
            self.env["account.move.reversal"]
            .with_context(active_ids=in_invoice.ids, active_model=in_invoice._name)
            .create({})
        )
        refund_wizard.write(
            {
                "refund_type": "percentage",
                "reason": "test",
                "percentage": 15,
                "l10n_latam_document_number": "B0400000001",
            }
        )
        result_invoice = self.env["account.move"].browse(
            refund_wizard.reverse_moves()["res_id"]
        )
        self.assertRecordValues(
            result_invoice.line_ids,
            [
                {"name": "test", "price_unit": 16.5},
                {"name": "", "price_unit": -16.5, "debit": 16.5, "credit": 0},
            ],
        )

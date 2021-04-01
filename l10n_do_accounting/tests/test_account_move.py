from odoo.tests.common import TransactionCase


class AccountMoveTest(TransactionCase):
    def init_invoice(
        self,
        move_type,
        products,
        journal,
        partner=False,
        document_number=None,
    ):
        if not partner:
            partner = self.env.ref("l10n_do_accounting.demo_partner_indexa")

        return self.env["account.move"].create(
            {
                "move_type": move_type,
                "l10n_latam_document_number": document_number,
                "partner_id": partner,
                "journal_id": journal.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": p.id,
                            "quantity": 1,
                        },
                    )
                    for p in products
                ],
            }
        )

    def setUp(self):
        super(AccountMoveTest, self).setUp()

        self.Move = self.env["account.move"]
        self.Product = self.env["product.product"]
        self.l10n_do_company = (
            self.env["res.company"]
            .search([])
            .filtered(lambda c: c.partner_id.country_id == self.env.ref("base.do"))
        )

        # move env user to DO company
        self.env.user.company_id = self.l10n_do_company.id

        # turn on fiscal journals
        self.sale_journal = self.Move.with_context(
            default_move_type="out_invoice", default_company_id=self.l10n_do_company.id
        )._get_default_journal()
        self.purchase_journal = self.Move.with_context(
            default_move_type="in_invoice", default_company_id=self.l10n_do_company.id
        )._get_default_journal()
        (self.sale_journal + self.purchase_journal).l10n_latam_use_documents = True

        # test products
        self.products = self.Product.create(
            [
                {
                    "name": "product_a",
                    "lst_price": 1000.0,
                },
                {
                    "name": "product_b",
                    "lst_price": 2000.0,
                },
            ]
        )

    def test_001_account_move_first_seq(self):
        """Check first internal generated sequence is enabled to be set manually"""

        invoice_1 = self.init_invoice(
            "out_invoice",
            self.products,
            self.sale_journal,
            document_number="B0100000001",
        )
        self.assertTrue(
            invoice_1.l10n_do_enable_first_sequence,
            "First fiscal invoice must enable document number input",
        )
        invoice_1._post()

        invoice_2 = self.init_invoice("out_invoice", self.products, self.sale_journal)
        self.assertFalse(
            invoice_2.l10n_do_enable_first_sequence,
            "Second fiscal invoice must disable document number input",
        )

        invoice_3 = self.init_invoice(
            "in_invoice",
            self.products,
            self.purchase_journal,
            partner=self.env.ref("l10n_do_accounting.demo_partner_jose"),
            document_number="B1100000001",
        )
        self.assertTrue(
            invoice_3.l10n_do_enable_first_sequence,
            "First fiscal invoice must enable document number input",
        )
        invoice_3._post()

        invoice_4 = self.init_invoice(
            "in_invoice",
            self.products,
            self.purchase_journal,
            partner=self.env.ref("l10n_do_accounting.demo_partner_jose"),
        )
        self.assertFalse(
            invoice_4.l10n_do_enable_first_sequence,
            "Second fiscal invoice must disable document number input",
        )

    def test_002_account_move_fiscal_seq(self):
        """
        Check both fiscal and internal invoice sequences are computed when post
        """

        self.init_invoice(
            "out_invoice",
            self.products,
            self.sale_journal,
            document_number="B0100000001",
        )._post()

        invoice_1 = self.init_invoice(
            "out_invoice",
            self.products,
            self.sale_journal,
        )
        invoice_1._post()
        self.assertRecordValues(
            invoice_1,
            [
                {
                    "name": "%s/%04d/0002"
                    % (
                        invoice_1.journal_id.code,
                        invoice_1.date.year,
                    ),
                    "l10n_latam_document_number": "B0100000002",
                }
            ],
        )

        invoice_2 = self.init_invoice(
            "in_invoice",
            self.products,
            self.purchase_journal,
            document_number="B0100000005",
        )
        invoice_2._post()
        self.assertRecordValues(
            invoice_2,
            [
                {
                    "name": "%s/%04d/0001"
                            % (
                                invoice_2.journal_id.code,
                                invoice_2.date.year,
                            ),
                    "l10n_latam_document_number": "B0100000005",
                }
            ],
        )

from odoo.tests import tagged
from odoo.tests.common import Form
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("external_l10n", "post_install", "-at_install", "-standard", "external")
class L10nDOTestsCommon(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref="l10n_do.do_chart_template"):
        super(L10nDOTestsCommon, cls).setUpClass(chart_template_ref=chart_template_ref)

        cls.do_company = cls.setup_company_data(
            "INDEXA SRL",
            chart_template=cls.env.ref(chart_template_ref),
            vat="131793916",
            street="dummy address",
            country_id=cls.env.ref("base.do").id,
        )["company"]
        cls.fiscal_partner = cls.env["res.partner"].create(
            {
                "name": "ITERATIVO SRL",
                "vat": "131566332",
                "l10n_do_dgii_tax_payer_type": "taxpayer",
                "country_id": cls.env.ref("base.do").id,
            }
        )
        cls.consumo_partner = cls.env["res.partner"].create(
            {
                "name": "JOSE LUIS LOPEZ",
                "vat": "22400559690",
                "l10n_do_dgii_tax_payer_type": "non_payer",
                "country_id": cls.env.ref("base.do").id,
            }
        )
        cls.special_partner = cls.env["res.partner"].create(
            {
                "name": "ZONA FRANCA INDUSTRIAL DE LAS AMERICAS S A",
                "vat": "101168481",
                "l10n_do_dgii_tax_payer_type": "special",
                "country_id": cls.env.ref("base.do").id,
            }
        )
        cls.gov_partner = cls.env["res.partner"].create(
            {
                "name": "MINISTERIO DE INDUSTRIA Y COMERCIO Y MIPYMES",
                "vat": "401007355",
                "l10n_do_dgii_tax_payer_type": "governmental",
                "country_id": cls.env.ref("base.do").id,
            }
        )
        cls.foreigner_partner = cls.env["res.partner"].create(
            {
                "name": "Azure Interior",
                "vat": "847898798",
                "l10n_do_dgii_tax_payer_type": "foreigner",
                "country_id": cls.env.ref("base.us").id,
            }
        )
        journals = cls.env["account.journal"].search(
            [
                ("type", "in", ("sale", "purchase")),
                ("company_id", "=", cls.do_company.id),
            ]
        )
        journals.write({"l10n_latam_use_documents": True})
        cls.fiscal_sale_journal = journals.filtered(lambda j: j.type == "sale")[0]
        cls.fiscal_purchase_journal = journals.filtered(lambda j: j.type == "purchase")[
            0
        ]
        cls.product_itbis_18 = cls.env["product.product"].create(
            {
                "name": "Product - Service",
                "lst_price": 100,
                "type": "service",
                "taxes_id": [(4, cls.do_company.account_sale_tax_id.id)],
            }
        )
        cls.do_document_type = {
            "fiscal": cls.env.ref("l10n_do_accounting.ncf_fiscal_client"),
            "consumer": cls.env.ref("l10n_do_accounting.ncf_consumer_supplier"),
            "debit_note": cls.env.ref("l10n_do_accounting.ncf_debit_note_client"),
            "credit_note": cls.env.ref("l10n_do_accounting.ncf_credit_note_client"),
            "informal": cls.env.ref("l10n_do_accounting.ncf_informal_supplier"),
            "unique": cls.env.ref("l10n_do_accounting.ncf_unique_client"),
            "minor": cls.env.ref("l10n_do_accounting.ncf_minor_supplier"),
            "special": cls.env.ref("l10n_do_accounting.ncf_special_client"),
            "governmental": cls.env.ref("l10n_do_accounting.ncf_gov_client"),
            "export": cls.env.ref("l10n_do_accounting.ncf_export_client"),
            "exterior": cls.env.ref("l10n_do_accounting.ncf_exterior_supplier"),
            "e-fiscal": cls.env.ref("l10n_do_accounting.ecf_fiscal_client"),
            "e-consumer": cls.env.ref("l10n_do_accounting.ecf_consumer_supplier"),
            "e-debit_note": cls.env.ref("l10n_do_accounting.ecf_debit_note_client"),
            "e-credit_note": cls.env.ref("l10n_do_accounting.ecf_credit_note_client"),
            "e-informal": cls.env.ref("l10n_do_accounting.ecf_informal_supplier"),
            "e-minor": cls.env.ref("l10n_do_accounting.ecf_minor_supplier"),
            "e-special": cls.env.ref("l10n_do_accounting.ecf_special_client"),
            "e-governmental": cls.env.ref("l10n_do_accounting.ecf_gov_client"),
            "e-export": cls.env.ref("l10n_do_accounting.ecf_export_client"),
            "e-exterior": cls.env.ref("l10n_do_accounting.ecf_exterior_supplier"),
        }

    def _create_l10n_do_invoice(self, data=None, invoice_type="out_invoice"):
        data = data or {}
        with Form(
            self.env["account.move"].with_context(default_move_type=invoice_type)
        ) as invoice_form:
            invoice_form.partner_id = data.get("partner", self.fiscal_partner)
            if "in_" not in invoice_type:
                invoice_form.journal_id = data.get("journal", self.fiscal_sale_journal)
            else:
                invoice_form.journal_id = self.fiscal_purchase_journal
            if data.get("invoice_date"):
                invoice_form.invoice_date = data.get("invoice_date")
            if data.get("document_type"):
                invoice_form.l10n_latam_document_type_id = data.get("document_type")
            if data.get("document_number"):
                invoice_form.l10n_latam_document_number = data.get("document_number")
            if data.get("currency"):
                invoice_form.currency_id = data.get("currency")
            if data.get("expense_type"):
                invoice_form.l10n_do_expense_type = data.get("expense_type")
            for line in data.get("lines", [{}]):
                with invoice_form.invoice_line_ids.new() as invoice_line_form:
                    invoice_line_form.product_id = line.get(
                        "product", self.product_itbis_18
                    )
                    invoice_line_form.quantity = line.get("quantity", 1)
                    invoice_line_form.price_unit = line.get("price_unit", 100)

                    ncf_type = invoice_form.l10n_latam_document_type_id.l10n_do_ncf_type
                    if ncf_type and ncf_type[-7:] == "special":
                        invoice_line_form.tax_ids.clear()
                    elif ncf_type and ncf_type[-8:] == "informal":
                        invoice_line_form.tax_ids.clear()
                        taxes = self.env["account.tax"].search(
                            [
                                ("company_id", "=", invoice_form.journal_id.id),
                                ("type_tax_use", "=", "purchase"),
                                ("amount", "in", (18, -18, -10)),
                            ],
                            limit=3,
                        )
                        for tax in taxes:
                            invoice_line_form.tax_ids.add(tax)
            invoice_form.invoice_date = invoice_form.date
        invoice = invoice_form.save()
        return invoice

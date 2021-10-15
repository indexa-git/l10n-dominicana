from . import common
from odoo.exceptions import RedirectWarning


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

    def test_002_invoice_ncf_types(self):

        # Fiscal Tax Payer
        ncf_sale_credito_fiscal_invoice = self._create_l10n_do_invoice(
            data={
                "document_number": "B0100000001",
            }
        )
        self.assertEqual(
            ncf_sale_credito_fiscal_invoice.l10n_latam_available_document_type_ids,
            self.do_document_type["fiscal"],
            "Tax Payer invoice must have only Credito Fiscal as available document type",
        )

        # Non Tax Payer
        ncf_sale_consumo_invoice = self._create_l10n_do_invoice(
            data={
                "partner": self.consumo_partner,
                "document_number": "B0200000001",
            }
        )
        self.assertEqual(
            ncf_sale_consumo_invoice.l10n_latam_available_document_type_ids,
            self.env["l10n_latam.document.type"].browse(
                (
                    self.do_document_type["consumer"] + self.do_document_type["unique"]
                ).ids
            ),
            "Non Tax Payer invoice must have Consumo and Unico Ingreso as available document type",
        )

        # Nonprofit Organization
        ncf_sale_special_invoice = self._create_l10n_do_invoice(
            data={
                "partner": self.special_partner,
                "document_number": "B1400000001",
            }
        )
        self.assertEqual(
            ncf_sale_special_invoice.l10n_latam_available_document_type_ids,
            self.do_document_type["special"],
            "Exempt from Tax Paying invoice must have Regimen Especial as available document type",
        )

        # Governmental
        ncf_sale_gov_invoice = self._create_l10n_do_invoice(
            data={
                "partner": self.gov_partner,
                "document_number": "B1500000001",
            }
        )
        self.assertEqual(
            ncf_sale_gov_invoice.l10n_latam_available_document_type_ids,
            self.do_document_type["governmental"],
            "Governmental invoice must have Regimen Especial as available document type",
        )

        # Foreigner
        ncf_sale_foreigner_invoice = self._create_l10n_do_invoice(
            data={
                "partner": self.foreigner_partner,
                # "document_number": "B0100000001",
            }
        )
        self.assertEqual(
            ncf_sale_foreigner_invoice.l10n_latam_available_document_type_ids,
            self.do_document_type["consumer"],
            "Foreigner invoice must have Consumo as available document type",
        )

from . import common
from odoo import fields
from odoo.tests import tagged
from odoo.exceptions import ValidationError
import psycopg2


@tagged("-at_install", "post_install")
class AccountMoveTest(common.L10nDOTestsCommon):
    def test_001_invoice_ncf_types(self):
        """
        Check NCF invoice get correct document types domain.
        Also checks manual document feature works correctly.
        """

        # # #
        #  Sale Documents
        # # #

        # Fiscal Tax Payer
        ncf_sale_credito_fiscal_invoice = self._create_l10n_do_invoice(
            data={
                "document_number": "B0100000001",
            }
        )
        self.assertEqual(
            ncf_sale_credito_fiscal_invoice.l10n_latam_available_document_type_ids,
            self.do_document_type["fiscal"],
            "Tax Payer invoice must have only Credito Fiscal as available "
            "document type",
        )

        self.assertFalse(
            ncf_sale_credito_fiscal_invoice.l10n_latam_manual_document_number
        )

        # Credit Note
        ncf_sale_credito_fiscal_invoice._post()
        fiscal_sale_credit_note_wizard = (
            self.env["account.move.reversal"]
            .with_context(
                active_ids=ncf_sale_credito_fiscal_invoice.ids,
                active_model="account.move",
            )
            .create(
                {
                    "l10n_do_refund_type": "percentage",
                    "l10n_do_percentage": "5",
                    "journal_id": ncf_sale_credito_fiscal_invoice[0].journal_id.id,
                }
            )
        )
        reverse_move_id = self.env["account.move"].browse(
            fiscal_sale_credit_note_wizard.reverse_moves()["res_id"]
        )
        self.assertFalse(reverse_move_id.l10n_latam_manual_document_number)
        self.assertEqual(
            reverse_move_id.l10n_latam_available_document_type_ids,
            self.do_document_type["credit_note"],
            "Non Tax Payer invoice must have Nota de Credito as available "
            "document type",
        )

        # Debit Note
        fiscal_sale_debit_note_wizard = (
            self.env["account.debit.note"]
            .with_context(
                active_ids=ncf_sale_credito_fiscal_invoice.ids,
                active_model="account.move",
            )
            .create(
                {
                    "l10n_do_debit_type": "percentage",
                    "l10n_do_percentage": "5",
                }
            )
        )
        debit_move_id = self.env["account.move"].browse(
            fiscal_sale_debit_note_wizard.create_debit()["res_id"]
        )
        self.assertFalse(debit_move_id.l10n_latam_manual_document_number)
        self.assertEqual(
            debit_move_id.l10n_latam_available_document_type_ids,
            self.do_document_type["debit_note"],
            "Tax Payer invoice must have Nota de Debito as available document type",
        )

        # Non Tax Payer
        ncf_sale_consumo_invoice = self._create_l10n_do_invoice(
            data={
                "partner": self.consumo_partner,
                "document_number": "B0200000001",
            }
        )
        self.assertFalse(ncf_sale_consumo_invoice.l10n_latam_manual_document_number)
        self.assertEqual(
            ncf_sale_consumo_invoice.l10n_latam_available_document_type_ids,
            self.env["l10n_latam.document.type"].browse(
                (
                    self.do_document_type["consumer"] + self.do_document_type["unique"]
                ).ids
            ),
            "Non Tax Payer invoice must have Consumo and Unico Ingreso as available "
            "document type",
        )

        # Nonprofit Organization
        ncf_sale_special_invoice = self._create_l10n_do_invoice(
            data={
                "partner": self.special_partner,
                "document_number": "B1400000001",
            }
        )
        self.assertFalse(ncf_sale_special_invoice.l10n_latam_manual_document_number)
        self.assertEqual(
            ncf_sale_special_invoice.l10n_latam_available_document_type_ids,
            self.do_document_type["special"],
            "Exempt from Tax Paying invoice must have Regimen Especial as available "
            "document type",
        )

        # Governmental
        ncf_sale_gov_invoice = self._create_l10n_do_invoice(
            data={
                "partner": self.gov_partner,
                "document_number": "B1500000001",
            }
        )
        self.assertFalse(ncf_sale_gov_invoice.l10n_latam_manual_document_number)
        self.assertEqual(
            ncf_sale_gov_invoice.l10n_latam_available_document_type_ids,
            self.do_document_type["governmental"],
            "Governmental invoice must have Gubernamental as available document type",
        )

        # Foreigner
        # you cannot have multiple draft invoices with the same ncf
        ncf_sale_consumo_invoice.unlink()
        ncf_sale_foreigner_invoice = self._create_l10n_do_invoice(
            data={
                "partner": self.foreigner_partner,
                "document_number": "B0200000001",
            }
        )
        self.assertFalse(ncf_sale_foreigner_invoice.l10n_latam_manual_document_number)
        self.assertEqual(
            ncf_sale_foreigner_invoice.l10n_latam_available_document_type_ids,
            self.env["l10n_latam.document.type"].browse(
                (
                    self.do_document_type["consumer"] + self.do_document_type["export"]
                ).ids
            ),
            "Foreigner invoice must have Consumo and Exportaciones as available "
            "document type",
        )

        # # #
        #  Purchase Documents
        # # #

        ncf_purchase_credito_fiscal_invoice = self._create_l10n_do_invoice(
            data={
                "document_number": "B0100000001",
                "expense_type": "02",
                "invoice_date": fields.Date.today(),
            },
            invoice_type="in_invoice",
        )
        self.assertTrue(
            ncf_purchase_credito_fiscal_invoice.l10n_latam_manual_document_number
        )
        self.assertEqual(
            ncf_purchase_credito_fiscal_invoice.l10n_latam_available_document_type_ids,
            self.env["l10n_latam.document.type"].browse(
                (
                    self.do_document_type["fiscal"] + self.do_document_type["e-fiscal"]
                ).ids
            ),
            "Tax Payer invoice must have only Credito Fiscal as available "
            "document type",
        )

        # Credit Note
        ncf_purchase_credito_fiscal_invoice._post()
        fiscal_purchase_credit_note_wizard = (
            self.env["account.move.reversal"]
            .with_context(
                active_ids=ncf_purchase_credito_fiscal_invoice.ids,
                active_model="account.move",
            )
            .create(
                {
                    "l10n_do_refund_type": "percentage",
                    "l10n_do_percentage": "5",
                    "l10n_latam_document_number": "B0400000001",
                    "journal_id": ncf_purchase_credito_fiscal_invoice[0].journal_id.id,
                }
            )
        )
        reverse_move_id = self.env["account.move"].browse(
            fiscal_purchase_credit_note_wizard.reverse_moves()["res_id"]
        )
        self.assertTrue(reverse_move_id.l10n_latam_manual_document_number)
        self.assertEqual(
            reverse_move_id.l10n_latam_available_document_type_ids,
            self.env["l10n_latam.document.type"].browse(
                (
                    self.do_document_type["credit_note"]
                    + self.do_document_type["e-credit_note"]
                ).ids
            ),
            "Non Tax Payer invoice must have Nota de Credito as available "
            "document type",
        )

        # Debit Note
        fiscal_purchase_debit_note_wizard = (
            self.env["account.debit.note"]
            .with_context(
                active_ids=ncf_purchase_credito_fiscal_invoice.ids,
                active_model="account.move",
            )
            .create(
                {
                    "l10n_do_debit_type": "percentage",
                    "l10n_do_percentage": "5",
                    "l10n_latam_document_number": "B0300000001",
                }
            )
        )
        debit_move_id = self.env["account.move"].browse(
            fiscal_purchase_debit_note_wizard.create_debit()["res_id"]
        )
        self.assertTrue(debit_move_id.l10n_latam_manual_document_number)
        self.assertEqual(
            debit_move_id.l10n_latam_available_document_type_ids,
            self.env["l10n_latam.document.type"].browse(
                (
                    self.do_document_type["debit_note"]
                    + self.do_document_type["e-debit_note"]
                ).ids
            ),
            "Tax Payer invoice must have Nota de Debito as available document type",
        )

        ncf_purchase_compra_invoice = self._create_l10n_do_invoice(
            data={
                "partner": self.consumo_partner,
                "document_number": "B1100000001",
                "expense_type": "02",
            },
            invoice_type="in_invoice",
        )
        self.assertFalse(ncf_purchase_compra_invoice.l10n_latam_manual_document_number)
        self.assertEqual(
            ncf_purchase_compra_invoice.l10n_latam_available_document_type_ids,
            self.env["l10n_latam.document.type"].browse(
                (self.do_document_type["informal"] + self.do_document_type["minor"]).ids
            ),
            "Non Tax Payer invoice must have only Comprobante de Compra and Gasto Menor"
            " as available document type",
        )

    def test_002_invoice_ecf_types(self):
        """
        Check ECF invoice get correct document types domain
        """

        self.do_company.l10n_do_ecf_issuer = True

        # # #
        #  Sale Documents
        # # #

        # Fiscal Tax Payer
        ecf_sale_credito_fiscal_invoice = self._create_l10n_do_invoice(
            data={"document_number": "E310000000001"}
        )
        self.assertFalse(
            ecf_sale_credito_fiscal_invoice.l10n_latam_manual_document_number
        )
        self.assertEqual(
            ecf_sale_credito_fiscal_invoice.l10n_latam_available_document_type_ids,
            self.do_document_type["e-fiscal"],
            "Tax Payer invoice must have only Credito Fiscal Electronica as available "
            "document type",
        )

        # Credit Note
        ecf_sale_credito_fiscal_invoice.with_context(l10n_do_active_test=True)._post()
        fiscal_sale_credit_note_wizard = (
            self.env["account.move.reversal"]
            .with_context(
                active_ids=ecf_sale_credito_fiscal_invoice.ids,
                active_model="account.move",
            )
            .create(
                {
                    "l10n_do_refund_type": "percentage",
                    "l10n_do_percentage": "5",
                    "journal_id": ecf_sale_credito_fiscal_invoice[0].journal_id.id,
                }
            )
        )
        reverse_move_id = self.env["account.move"].browse(
            fiscal_sale_credit_note_wizard.reverse_moves()["res_id"]
        )
        self.assertFalse(reverse_move_id.l10n_latam_manual_document_number)
        self.assertEqual(
            reverse_move_id.l10n_latam_available_document_type_ids,
            self.do_document_type["e-credit_note"],
            "Non Tax Payer invoice must have Nota de Credito Electronica as available "
            "document type",
        )

        # Debit Note
        fiscal_sale_debit_note_wizard = (
            self.env["account.debit.note"]
            .with_context(
                active_ids=ecf_sale_credito_fiscal_invoice.ids,
                active_model="account.move",
            )
            .create(
                {
                    "l10n_do_debit_type": "percentage",
                    "l10n_do_percentage": "5",
                }
            )
        )
        debit_move_id = self.env["account.move"].browse(
            fiscal_sale_debit_note_wizard.create_debit()["res_id"]
        )
        self.assertFalse(debit_move_id.l10n_latam_manual_document_number)
        self.assertEqual(
            debit_move_id.l10n_latam_available_document_type_ids,
            self.do_document_type["e-debit_note"],
            "Tax Payer invoice must have Nota de Debito Electronica as available "
            "document type",
        )

        # Non Tax Payer
        ecf_sale_consumo_invoice = self._create_l10n_do_invoice(
            data={
                "partner": self.consumo_partner,
                "document_number": "E320000000001",
            }
        )
        self.assertFalse(ecf_sale_consumo_invoice.l10n_latam_manual_document_number)
        self.assertEqual(
            ecf_sale_consumo_invoice.l10n_latam_available_document_type_ids,
            self.do_document_type["e-consumer"],
            "Non Tax Payer invoice must have Consumo Electronico as available "
            "document type",
        )

        # Nonprofit Organization
        ecf_sale_special_invoice = self._create_l10n_do_invoice(
            data={
                "partner": self.special_partner,
                "document_number": "E440000000001",
            }
        )
        self.assertFalse(ecf_sale_special_invoice.l10n_latam_manual_document_number)
        self.assertEqual(
            ecf_sale_special_invoice.l10n_latam_available_document_type_ids,
            self.do_document_type["e-special"],
            "Exempt from Tax Paying invoice must have Regimen Especial Electronico as "
            "available document type",
        )

        # Governmental
        ecf_sale_gov_invoice = self._create_l10n_do_invoice(
            data={
                "partner": self.gov_partner,
                "document_number": "E450000000001",
            }
        )
        self.assertFalse(ecf_sale_gov_invoice.l10n_latam_manual_document_number)
        self.assertEqual(
            ecf_sale_gov_invoice.l10n_latam_available_document_type_ids,
            self.do_document_type["e-governmental"],
            "Governmental invoice must have Gubernamental Electronica as available "
            "document type",
        )

        # Foreigner
        # you cannot have multiple draft invoices with the same ncf
        ecf_sale_consumo_invoice.unlink()
        ecf_sale_foreigner_invoice = self._create_l10n_do_invoice(
            data={
                "partner": self.foreigner_partner,
                "document_number": "E320000000001",
            }
        )
        self.assertFalse(ecf_sale_foreigner_invoice.l10n_latam_manual_document_number)
        self.assertEqual(
            ecf_sale_foreigner_invoice.l10n_latam_available_document_type_ids,
            self.env["l10n_latam.document.type"].browse(
                (
                    self.do_document_type["e-consumer"]
                    + self.do_document_type["e-export"]
                ).ids
            ),
            "Foreigner invoice must have Consumo Electronica and Exportaciones "
            "Electronica as available document type",
        )

        # # #
        #  Purchase Documents
        # # #

        ecf_purchase_credito_fiscal_invoice = self._create_l10n_do_invoice(
            data={
                "document_number": "E310000000001",
                "expense_type": "02",
                "document_type": self.do_document_type["e-fiscal"],
                "invoice_date": fields.Date.today(),
            },
            invoice_type="in_invoice",
        )
        self.assertTrue(
            ecf_purchase_credito_fiscal_invoice.l10n_latam_manual_document_number
        )
        self.assertEqual(
            ecf_purchase_credito_fiscal_invoice.l10n_latam_available_document_type_ids,
            self.env["l10n_latam.document.type"].browse(
                (
                    self.do_document_type["fiscal"] + self.do_document_type["e-fiscal"]
                ).ids
            ),
            "Tax Payer invoice must have only Credito Fiscal as available "
            "document type",
        )

        # Credit Note
        ecf_purchase_credito_fiscal_invoice.with_context(
            l10n_do_active_test=True
        )._post()
        fiscal_purchase_credit_note_wizard = (
            self.env["account.move.reversal"]
            .with_context(
                active_ids=ecf_purchase_credito_fiscal_invoice.ids,
                active_model="account.move",
            )
            .create(
                {
                    "l10n_do_refund_type": "percentage",
                    "l10n_do_percentage": "5",
                    "l10n_latam_document_number": "B0400000001",
                    "journal_id": ecf_purchase_credito_fiscal_invoice[0].journal_id.id,
                }
            )
        )
        reverse_move_id = self.env["account.move"].browse(
            fiscal_purchase_credit_note_wizard.reverse_moves()["res_id"]
        )
        self.assertTrue(reverse_move_id.l10n_latam_manual_document_number)
        self.assertEqual(
            reverse_move_id.l10n_latam_available_document_type_ids,
            self.env["l10n_latam.document.type"].browse(
                (
                    self.do_document_type["credit_note"]
                    + self.do_document_type["e-credit_note"]
                ).ids
            ),
            "Non Tax Payer invoice must have Nota de Credito and Nota de Credito "
            "Electronica as available document type",
        )

        # Debit Note
        fiscal_purchase_debit_note_wizard = (
            self.env["account.debit.note"]
            .with_context(
                active_ids=ecf_purchase_credito_fiscal_invoice.ids,
                active_model="account.move",
            )
            .create(
                {
                    "l10n_do_debit_type": "percentage",
                    "l10n_do_percentage": "5",
                    "l10n_latam_document_number": "B0300000001",
                }
            )
        )
        debit_move_id = self.env["account.move"].browse(
            fiscal_purchase_debit_note_wizard.create_debit()["res_id"]
        )
        self.assertTrue(debit_move_id.l10n_latam_manual_document_number)
        self.assertEqual(
            debit_move_id.l10n_latam_available_document_type_ids,
            self.env["l10n_latam.document.type"].browse(
                (
                    self.do_document_type["debit_note"]
                    + self.do_document_type["e-debit_note"]
                ).ids
            ),
            "Tax Payer invoice must have Nota de Debito and Nota de Debito "
            "Electronica as available document type",
        )

        ecf_purchase_compra_invoice = self._create_l10n_do_invoice(
            data={
                "partner": self.consumo_partner,
                "document_number": "E410000000001",
                "expense_type": "02",
            },
            invoice_type="in_invoice",
        )
        self.assertFalse(ecf_purchase_compra_invoice.l10n_latam_manual_document_number)
        self.assertEqual(
            ecf_purchase_compra_invoice.l10n_latam_available_document_type_ids,
            self.env["l10n_latam.document.type"].browse(
                (
                    self.do_document_type["e-informal"]
                    + self.do_document_type["e-minor"]
                ).ids
            ),
            "Non Tax Payer invoice must have only Comprobante de Compra Electronica "
            "and Gasto Menor Electronica as available document type",
        )

    def test_003_enable_first_sequence(self):
        """
        Check enable first sequence feature works properly
        """
        # Sale invoice
        sale_invoice_1_id = self._create_l10n_do_invoice(
            data={
                "document_number": "B0100000001",
            }
        )
        self.assertTrue(sale_invoice_1_id.l10n_do_enable_first_sequence)
        sale_invoice_1_id._post()

        sale_invoice_2_id = self._create_l10n_do_invoice()
        self.assertFalse(sale_invoice_2_id.l10n_do_enable_first_sequence)

        # Purchase invoice
        purchase_invoice_1_id = self._create_l10n_do_invoice(
            data={
                "partner": self.consumo_partner,
                "document_number": "B1100000001",
                "expense_type": "02",
                "invoice_date": fields.Date.today(),
            },
            invoice_type="in_invoice",
        )
        self.assertTrue(purchase_invoice_1_id.l10n_do_enable_first_sequence)
        purchase_invoice_1_id._post()

        purchase_invoice_2_id = self._create_l10n_do_invoice(
            data={
                "partner": self.consumo_partner,
                "expense_type": "02",
            },
            invoice_type="in_invoice",
        )
        self.assertFalse(purchase_invoice_2_id.l10n_do_enable_first_sequence)

    def test_004_is_ecf_invoice(self):
        """
        Check Is ECF Invoice feature works properly
        """
        sale_invoice_1_id = self._create_l10n_do_invoice(
            data={
                "document_number": "B0100000001",
            }
        )
        self.assertFalse(sale_invoice_1_id.is_ecf_invoice)

        self.do_company.l10n_do_ecf_issuer = True
        sale_invoice_2_id = self._create_l10n_do_invoice(
            data={"document_number": "E310000000001"}
        )
        self.assertTrue(sale_invoice_2_id.is_ecf_invoice)

    def test_005_company_in_contingency(self):
        """
        Check Company in Contingency feature works properly
        """
        self.do_company.l10n_do_ecf_issuer = True
        sale_invoice_1_id = self._create_l10n_do_invoice(
            data={
                "document_number": "E310000000001",
            }
        )
        sale_invoice_1_id.with_context(l10n_do_active_test=True)._post()

        self.do_company.l10n_do_ecf_issuer = False

        sale_invoice_2_id = self._create_l10n_do_invoice(
            data={
                "document_number": "B0100000001",
            }
        )
        self.assertTrue(sale_invoice_2_id.l10n_do_company_in_contingency)

    def test_006_invoice_electronic_stamp(self):
        """
        Check invoice electronic stamp feature works properly
        """
        stamp = (
            "https%3A%2F%2Fecf.dgii.gov.do%2FTesteCF%2FConsultaTimbre%3FRncEmisor"
            "%3D131793916%26RncComprador%3D131566332%26ENCF%3DE310000000001%26Fec"
            "haEmision%3D16-10-2021%26MontoTotal%3D118%26FechaFirma%3D16-10-2021+"
            "00%3A00%3A00%26CodigoSeguridad%3Du83ac1"
        )

        sign_date = "2021-10-16"
        self.do_company.l10n_do_ecf_issuer = True
        sale_invoice_1_id = self._create_l10n_do_invoice(
            data={
                "document_number": "E310000000001",
                "invoice_date": sign_date,
            }
        )
        sale_invoice_1_id.write(
            {
                "l10n_do_ecf_security_code": "u83ac1",
                "l10n_do_ecf_sign_date": sign_date,
            }
        )
        sale_invoice_1_id.with_context(l10n_do_active_test=True)._post()
        self.assertEqual(sale_invoice_1_id.l10n_do_electronic_stamp, stamp)

    def test_007_unique_sequence_number(self):
        """
        Check unique sequence number constraint works properly.
        It is also James Bond favorite test.
        """

        invoice_id = self._create_l10n_do_invoice(
            data={
                "document_number": "B0100000001",
            }
        )
        invoice_id._post()

        invoice_2 = self._create_l10n_do_invoice()
        invoice_2._post()
        with self.assertRaises(psycopg2.errors.UniqueViolation):
            invoice_2.write({"l10n_do_fiscal_number": "B0100000001"})

    def test_008_check_sequence(self):
        """
        Check invoices get right internal & fiscal sequences
        """

        sale_invoice_1_id = self._create_l10n_do_invoice(
            data={
                "document_number": "B0100000001",
            }
        )
        sale_invoice_1_id._post()
        self.assertEqual(
            sale_invoice_1_id.name, "INV/%s/0001" % fields.Date.today().year
        )
        self.assertEqual(sale_invoice_1_id.l10n_do_fiscal_number, "B0100000001")

        sale_invoice_2_id = self._create_l10n_do_invoice()
        sale_invoice_2_id._post()
        self.assertEqual(
            sale_invoice_2_id.name, "INV/%s/0002" % fields.Date.today().year
        )
        self.assertEqual(sale_invoice_2_id.l10n_do_fiscal_number, "B0100000002")

        purchase_invoice_1_id = self._create_l10n_do_invoice(
            data={
                "document_number": "B0100000001",
                "expense_type": "02",
                "invoice_date": fields.Date.today(),
            },
            invoice_type="in_invoice",
        )
        purchase_invoice_1_id._post()
        self.assertEqual(
            purchase_invoice_1_id.name, "BILL/%s/0001" % fields.Date.today().year
        )
        self.assertEqual(purchase_invoice_1_id.l10n_do_fiscal_number, "B0100000001")

        purchase_invoice_2_id = self._create_l10n_do_invoice(
            data={
                "partner": self.consumo_partner,
                "document_number": "B1100000001",
                "expense_type": "02",
                "invoice_date": fields.Date.today(),
            },
            invoice_type="in_invoice",
        )
        purchase_invoice_2_id._post()
        self.assertEqual(
            purchase_invoice_2_id.name, "BILL/%s/0002" % fields.Date.today().year
        )
        self.assertEqual(purchase_invoice_2_id.l10n_do_fiscal_number, "B1100000001")

    def test_009_invoice_sequence(self):
        invoice_1 = self._create_l10n_do_invoice(
            data={
                "document_number": "B0100000001",
            }
        )
        self.assertEqual(invoice_1.name, "INV/%s/0001" % invoice_1.date.year)
        invoice_1._post()
        self.assertEqual(invoice_1.l10n_do_fiscal_number, "B0100000001")

        invoice_2 = self._create_l10n_do_invoice()
        invoice_2._post()
        self.assertEqual(invoice_2.name, "INV/%s/0002" % invoice_2.date.year)
        self.assertEqual(invoice_2.l10n_do_fiscal_number, "B0100000002")

        # Unit test to verify if the invoice number or document number is repeated
        invoice_3 = self._create_l10n_do_invoice(
            data={
                "invoice_date": "2023-05-08",
            }
        )
        invoice_3._post()
        self.assertEqual(invoice_3.name, "INV/%s/0001" % invoice_3.date.year)
        self.assertNotEqual(invoice_3.l10n_do_fiscal_number, "B0100000001")
        self.assertEqual(invoice_3.l10n_do_fiscal_number, "B0100000003")

    def test_010_ncf_format(self):
        with self.assertRaises(ValidationError):
            self._create_l10n_do_invoice(data={"document_number": "E0100000001"})

        self.do_company.l10n_do_ecf_issuer = True

        with self.assertRaises(ValidationError):
            self._create_l10n_do_invoice(data={"document_number": "B310000000001"})

    def test_011_get_l10n_do_line_amounts(self):
        invoice_1 = self._create_l10n_do_invoice(
            data={
                "document_number": "B0100000001",
            }
        )
        self.assertDictEqual(
            invoice_1._get_l10n_do_amounts(),
            {
                "base_amount": 100.0,
                "exempt_amount": 0,
                "isr_withholding_amount": 0,
                "isr_withholding_base_amount": 0,
                "itbis_0_base_amount": 0,
                "itbis_0_tax_amount": 0,
                "itbis_16_base_amount": 0,
                "itbis_16_tax_amount": 0,
                "itbis_18_base_amount": 100.0,
                "itbis_18_tax_amount": 18.0,
                "itbis_withholding_amount": 0,
                "itbis_withholding_base_amount": 0,
                "l10n_do_invoice_total": 118.0,
            },
        )

        invoice_2 = self._create_l10n_do_invoice(
            data={
                "partner": self.consumo_partner,
                "document_number": "B1100000001",
                "expense_type": "02",
            },
            invoice_type="in_invoice",
        )

        self.assertDictEqual(
            invoice_2._get_l10n_do_amounts(),
            {
                "base_amount": 100.0,
                "exempt_amount": 0,
                "isr_withholding_amount": 10.0,
                "isr_withholding_base_amount": 100.0,
                "itbis_0_base_amount": 0,
                "itbis_0_tax_amount": 0,
                "itbis_16_base_amount": 0,
                "itbis_16_tax_amount": 0,
                "itbis_18_base_amount": 100.0,
                "itbis_18_tax_amount": 18.0,
                "itbis_withholding_amount": 18.0,
                "itbis_withholding_base_amount": 100.0,
                "l10n_do_invoice_total": 118.0,
            },
        )

        invoice_3 = self._create_l10n_do_invoice(
            data={
                "document_number": "B0100000002",
                "currency": self.usd_currency,
            }
        )

        self.assertDictEqual(
            invoice_3._get_l10n_do_amounts(),
            {
                "base_amount": 100.0,
                "base_amount_currency": 5900.000000825999,
                "exempt_amount": 0,
                "exempt_amount_currency": 0.0,
                "isr_withholding_amount": 0,
                "isr_withholding_amount_currency": 0.0,
                "isr_withholding_base_amount": 0,
                "isr_withholding_base_amount_currency": 0.0,
                "itbis_0_base_amount": 0,
                "itbis_0_base_amount_currency": 0.0,
                "itbis_0_tax_amount": 0,
                "itbis_0_tax_amount_currency": 0.0,
                "itbis_16_base_amount": 0,
                "itbis_16_base_amount_currency": 0.0,
                "itbis_16_tax_amount": 0,
                "itbis_16_tax_amount_currency": 0.0,
                "itbis_18_base_amount": 100.0,
                "itbis_18_base_amount_currency": 5900.000000825999,
                "itbis_18_tax_amount": 18.0,
                "itbis_18_tax_amount_currency": 1062.0000001486799,
                "itbis_withholding_amount": 0,
                "itbis_withholding_amount_currency": 0.0,
                "itbis_withholding_base_amount": 0,
                "itbis_withholding_base_amount_currency": 0.0,
                "l10n_do_invoice_total": 118.0,
                "l10n_do_invoice_total_currency": 6962.000000974679,
            },
        )

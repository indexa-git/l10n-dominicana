from . import common


class AccountMoveTest(common.L10nDOTestsCommon):
    def test_001_invoice_ncf_types(self):
        """
        Check NCF invoice get correct document types domain
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
                    "refund_type": "percentage",
                    "percentage": "5",
                }
            )
        )
        reverse_move_id = self.env["account.move"].browse(
            fiscal_sale_credit_note_wizard.reverse_moves()["res_id"]
        )
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
        self.assertEqual(
            ncf_sale_gov_invoice.l10n_latam_available_document_type_ids,
            self.do_document_type["governmental"],
            "Governmental invoice must have Gubernamental as available document type",
        )

        # Foreigner
        ncf_sale_foreigner_invoice = self._create_l10n_do_invoice(
            data={
                "partner": self.foreigner_partner,
                "document_number": "B0200000001",
            }
        )
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
            },
            invoice_type="in_invoice",
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
                    "refund_type": "percentage",
                    "percentage": "5",
                    "l10n_latam_document_number": "B0400000001",
                }
            )
        )
        reverse_move_id = self.env["account.move"].browse(
            fiscal_purchase_credit_note_wizard.reverse_moves()["res_id"]
        )
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
        self.assertEqual(
            ecf_sale_credito_fiscal_invoice.l10n_latam_available_document_type_ids,
            self.do_document_type["e-fiscal"],
            "Tax Payer invoice must have only Credito Fiscal Electronica as available "
            "document type",
        )

        # Credit Note
        ecf_sale_credito_fiscal_invoice._post()
        fiscal_sale_credit_note_wizard = (
            self.env["account.move.reversal"]
            .with_context(
                active_ids=ecf_sale_credito_fiscal_invoice.ids,
                active_model="account.move",
            )
            .create(
                {
                    "refund_type": "percentage",
                    "percentage": "5",
                }
            )
        )
        reverse_move_id = self.env["account.move"].browse(
            fiscal_sale_credit_note_wizard.reverse_moves()["res_id"]
        )
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
        self.assertEqual(
            ecf_sale_gov_invoice.l10n_latam_available_document_type_ids,
            self.do_document_type["e-governmental"],
            "Governmental invoice must have Gubernamental Electronica as available "
            "document type",
        )

        # Foreigner
        ecf_sale_foreigner_invoice = self._create_l10n_do_invoice(
            data={
                "partner": self.foreigner_partner,
                "document_number": "E320000000001",
            }
        )
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
            },
            invoice_type="in_invoice",
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
        ecf_purchase_credito_fiscal_invoice._post()
        fiscal_purchase_credit_note_wizard = (
            self.env["account.move.reversal"]
            .with_context(
                active_ids=ecf_purchase_credito_fiscal_invoice.ids,
                active_model="account.move",
            )
            .create(
                {
                    "refund_type": "percentage",
                    "percentage": "5",
                    "l10n_latam_document_number": "B0400000001",
                }
            )
        )
        reverse_move_id = self.env["account.move"].browse(
            fiscal_purchase_credit_note_wizard.reverse_moves()["res_id"]
        )
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

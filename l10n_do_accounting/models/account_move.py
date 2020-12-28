from werkzeug import urls

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, AccessError


class AccountMove(models.Model):
    _inherit = "account.move"

    @property
    def _sequence_fixed_regex(self):
        if self.l10n_latam_country_code == "DO" and self.l10n_latam_use_documents:
            return r"^(?P<prefix1>.*?)(?P<seq>\d{0,8})(?P<suffix>\D*?)$"
        return super(AccountMove, self)._sequence_fixed_regex

    def _get_l10n_do_cancellation_type(self):
        """ Return the list of cancellation types required by DGII. """
        return [
            ("01", _("01 - Pre-printed Invoice Impairment")),
            ("02", _("02 - Printing Errors (Pre-printed Invoice)")),
            ("03", _("03 - Defective Printing")),
            ("04", _("04 - Correction of Product Information")),
            ("05", _("05 - Product Change")),
            ("06", _("06 - Product Return")),
            ("07", _("07 - Product Omission")),
            ("08", _("08 - NCF Sequence Errors")),
            ("09", _("09 - For Cessation of Operations")),
            ("10", _("10 - Lossing or Hurting Of Counterfoil")),
        ]

    def _get_l10n_do_ecf_modification_code(self):
        """ Return the list of e-CF modification codes required by DGII. """
        return [
            ("1", _("01 - Total Cancellation")),
            ("2", _("02 - Text Correction")),
            ("3", _("03 - Amount correction")),
            ("4", _("04 - NCF replacement issued in contingency")),
            ("5", _("05 - Reference Electronic Consumer Invoice")),
        ]

    def _get_l10n_do_income_type(self):
        """ Return the list of income types required by DGII. """
        return [
            ("01", _("01 - Operational Incomes")),
            ("02", _("02 - Financial Incomes")),
            ("03", _("03 - Extraordinary Incomes")),
            ("04", _("04 - Leasing Incomes")),
            ("05", _("05 - Income for Selling Depreciable Assets")),
            ("06", _("06 - Other Incomes")),
        ]

    l10n_do_expense_type = fields.Selection(
        selection=lambda self: self.env["res.partner"]._get_l10n_do_expense_type(),
        string="Cost & Expense Type",
    )

    l10n_do_cancellation_type = fields.Selection(
        selection="_get_l10n_do_cancellation_type",
        string="Cancellation Type",
        copy=False,
    )

    l10n_do_income_type = fields.Selection(
        selection="_get_l10n_do_income_type",
        string="Income Type",
        copy=False,
        default=lambda self: self._context.get("l10n_do_income_type", "01"),
    )

    l10n_do_origin_ncf = fields.Char(
        string="Modifies",
    )

    is_ecf_invoice = fields.Boolean(
        compute="_compute_is_ecf_invoice",
        store=True,
    )
    l10n_do_ecf_modification_code = fields.Selection(
        selection="_get_l10n_do_ecf_modification_code",
        string="e-CF Modification Code",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    l10n_do_ecf_security_code = fields.Char(string="e-CF Security Code", copy=False)
    l10n_do_ecf_sign_date = fields.Datetime(string="e-CF Sign Date", copy=False)
    l10n_do_electronic_stamp = fields.Char(
        string="Electronic Stamp",
        compute="_compute_l10n_do_electronic_stamp",
        store=True,
    )
    l10n_do_company_in_contingency = fields.Boolean(
        string="Company in contingency",
        compute="_compute_company_in_contingency",
    )
    l10n_latam_country_code = fields.Char(
        "Country Code",
        related="company_id.country_id.code",
    )

    @api.depends(
        "l10n_latam_country_code",
        "l10n_latam_document_type_id.l10n_do_ncf_type",
    )
    def _compute_is_ecf_invoice(self):
        for invoice in self:
            invoice.is_ecf_invoice = (
                invoice.l10n_latam_country_code == "DO"
                and invoice.l10n_latam_document_type_id
                and invoice.l10n_latam_document_type_id.l10n_do_ncf_type[:2] == "e-"
            )

    @api.depends("company_id", "company_id.l10n_do_ecf_issuer")
    def _compute_company_in_contingency(self):
        for invoice in self:
            ecf_invoices = self.search([("is_ecf_invoice", "=", True)], limit=1)
            invoice.l10n_do_company_in_contingency = bool(
                ecf_invoices and not invoice.company_id.l10n_do_ecf_issuer
            )

    @api.depends("l10n_do_ecf_security_code", "l10n_do_ecf_sign_date", "invoice_date")
    @api.depends_context("l10n_do_ecf_service_env")
    def _compute_l10n_do_electronic_stamp(self):

        for invoice in self.filtered(
            lambda i: i.is_ecf_invoice
            and i.l10n_do_ecf_security_code
            and i.l10n_do_ecf_sign_date
        ):

            ecf_service_env = self.env.context.get("l10n_do_ecf_service_env", "CerteCF")
            doc_code_prefix = invoice.l10n_latam_document_type_id.doc_code_prefix
            has_sign_date = doc_code_prefix != "E32" or (
                doc_code_prefix == "E32" and invoice.amount_total_signed >= 250000
            )

            qr_string = "https://ecf.dgii.gov.do/%s/ConsultaTimbre?" % ecf_service_env
            qr_string += "RncEmisor=%s&" % invoice.company_id.vat or ""
            qr_string += (
                "RncComprador=%s&" % invoice.commercial_partner_id.vat
                if invoice.l10n_latam_document_type_id.doc_code_prefix[1:] != "43"
                else invoice.company_id.vat
            )
            qr_string += "ENCF=%s&" % invoice.ref or ""
            qr_string += "FechaEmision=%s&" % (
                invoice.invoice_date or fields.Date.today()
            ).strftime("%d-%m-%Y")
            qr_string += "MontoTotal=%s&" % (
                "%f" % abs(invoice.amount_total_signed)
            ).rstrip("0").rstrip(".")

            # DGII doesn't want FechaFirma if Consumo Electronico and < 250K
            # ¯\_(ツ)_/¯
            if has_sign_date:
                qr_string += (
                    "FechaFirma=%s&"
                    % fields.Datetime.context_timestamp(
                        self.with_context(tz="America/Santo_Domingo"),
                        invoice.l10n_do_ecf_sign_date,
                    ).strftime("%d-%m-%Y %H:%M:%S")
                )

            qr_string += "CodigoSeguridad=%s" % invoice.l10n_do_ecf_security_code or ""

            invoice.l10n_do_electronic_stamp = urls.url_quote_plus(qr_string)

    def button_cancel(self):

        fiscal_invoice = self.filtered(
            lambda inv: inv.l10n_latam_country_code == "DO"
            and self.move_type[-6:] in ("nvoice", "refund")
            and inv.l10n_latam_use_documents
        )

        if len(fiscal_invoice) > 1:
            raise ValidationError(
                _("You cannot cancel multiple fiscal invoices at a time.")
            )

        if fiscal_invoice and not self.env.user.has_group(
            "l10n_do_accounting.group_l10n_do_fiscal_invoice_cancel"
        ):
            raise AccessError(_("You are not allowed to cancel Fiscal Invoices"))

        if fiscal_invoice:
            action = self.env.ref(
                "l10n_do_accounting.action_account_move_cancel"
            ).read()[0]
            action["context"] = {"default_move_id": fiscal_invoice.id}
            return action

        return super(AccountMove, self).button_cancel()

    def action_reverse(self):

        fiscal_invoice = self.filtered(
            lambda inv: inv.l10n_latam_country_code == "DO"
            and self.move_type[-6:] in ("nvoice", "refund")
        )
        if fiscal_invoice and not self.env.user.has_group(
            "l10n_do_accounting.group_l10n_do_fiscal_credit_note"
        ):
            raise AccessError(_("You are not allowed to issue Fiscal Credit Notes"))

        return super(AccountMove, self).action_reverse()

    @api.onchange("l10n_latam_document_type_id", "l10n_latam_document_number")
    def _inverse_l10n_latam_document_number(self):
        for rec in self.filtered("l10n_latam_document_type_id"):
            if not rec.l10n_latam_document_number:
                rec.ref = ""
            else:
                document_type_id = rec.l10n_latam_document_type_id
                if document_type_id.l10n_do_ncf_type:
                    document_number = document_type_id._format_document_number(
                        rec.l10n_latam_document_number
                    )
                else:
                    document_number = rec.l10n_latam_document_number

                if rec.l10n_latam_document_number != document_number:
                    rec.l10n_latam_document_number = document_number
                rec.ref = document_number
        super(
            AccountMove, self.filtered(lambda m: m.l10n_latam_country_code != "DO")
        )._inverse_l10n_latam_document_number()

    def _get_l10n_latam_documents_domain(self):
        self.ensure_one()
        domain = super()._get_l10n_latam_documents_domain()
        if (
            self.journal_id.l10n_latam_use_documents
            and self.journal_id.company_id.country_id == self.env.ref("base.do")
        ):
            ncf_types = self.journal_id._get_journal_ncf_types(
                counterpart_partner=self.partner_id.commercial_partner_id, invoice=self
            )
            domain += [
                "|",
                ("l10n_do_ncf_type", "=", False),
                ("l10n_do_ncf_type", "in", ncf_types),
            ]
            codes = self.journal_id._get_journal_codes()
            if codes:
                domain.append(("code", "in", codes))
        return domain

    @api.constrains("move_type", "l10n_latam_document_type_id")
    def _check_invoice_type_document_type(self):
        super()._check_invoice_type_document_type()
        for rec in self.filtered(
            lambda r: r.company_id.country_id == self.env.ref("base.do")
            and r.l10n_latam_document_type_id
        ):
            partner_vat = rec.partner_id.vat
            l10n_latam_document_type = rec.l10n_latam_document_type_id
            if not partner_vat and l10n_latam_document_type.is_vat_required:
                raise ValidationError(
                    _(
                        "A VAT is mandatory for this type of NCF. "
                        "Please set the current VAT of this client"
                    )
                )

            elif rec.move_type in ("out_invoice", "out_refund"):
                if (
                    rec.amount_untaxed_signed >= 250000
                    and l10n_latam_document_type.l10n_do_ncf_type[-7:] != "special"
                    and not rec.partner_id.vat
                ):
                    raise UserError(
                        _(
                            "If the invoice amount is greater than RD$250,000.00 "
                            "the customer should have a VAT to validate the invoice"
                        )
                    )

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if (
            self.company_id.country_id == self.env.ref("base.do")
            and self.l10n_latam_document_type_id
            and self.move_type == "in_invoice"
            and self.partner_id
        ):
            self.l10n_do_expense_type = (
                self.partner_id.l10n_do_expense_type
                if not self.l10n_do_expense_type
                else self.l10n_do_expense_type
            )

        return super(AccountMove, self)._onchange_partner_id()

    def _reverse_move_vals(self, default_values, cancel=True):

        ctx = self.env.context
        amount = ctx.get("amount")
        percentage = ctx.get("percentage")
        refund_type = ctx.get("refund_type")
        reason = ctx.get("reason")
        l10n_do_ecf_modification_code = ctx.get("l10n_do_ecf_modification_code")

        res = super(AccountMove, self)._reverse_move_vals(
            default_values=default_values, cancel=cancel
        )

        if self.l10n_latam_country_code == "DO":
            res["l10n_do_origin_ncf"] = self.l10n_latam_document_number
            res["l10n_do_ecf_modification_code"] = l10n_do_ecf_modification_code

        if refund_type in ("percentage", "fixed_amount"):
            price_unit = (
                amount
                if refund_type == "fixed_amount"
                else self.amount_untaxed * (percentage / 100)
            )
            res["line_ids"] = False
            res["invoice_line_ids"] = [
                (0, 0, {"name": reason or _("Refund"), "price_unit": price_unit})
            ]
        return res

    def _is_manual_document_number(self, journal):

        if (
            self.company_id.country_id == self.env.ref("base.do")
            and self.l10n_latam_document_type_id
        ):
            return self.move_type in (
                "in_invoice",
                "in_refund",
            ) and self.l10n_latam_document_type_id.l10n_do_ncf_type not in (
                "minor",
                "e-minor",
                "informal",
                "e-informal",
            )

        return super(AccountMove, self)._is_manual_document_number(journal=journal)

    def _post(self, soft=True):

        res = super()._post(soft)

        non_payer_type_invoices = self.filtered(
            lambda inv: inv.company_id.country_id == self.env.ref("base.do")
            and inv.l10n_latam_use_documents
            and not inv.partner_id.l10n_do_dgii_tax_payer_type
        )
        if non_payer_type_invoices:
            raise ValidationError(_("Fiscal invoices require partner fiscal type"))

        return res

    def _l10n_do_get_formatted_sequence(self):
        document_type_id = self.l10n_latam_document_type_id
        return "%s%s" % (
            document_type_id.doc_code_prefix,
            "".zfill(
                10 if str(document_type_id.l10n_do_ncf_type).startswith("e-") else 8
            ),
        )

    def _get_starting_sequence(self):
        if (
            self.journal_id.l10n_latam_use_documents
            and self.env.company.country_id.code == "DO"
            and self.l10n_latam_document_type_id
        ):
            return self._l10n_do_get_formatted_sequence()

        return super()._get_starting_sequence()

    def _get_last_sequence_domain(self, relaxed=False):
        where_string, param = super(AccountMove, self)._get_last_sequence_domain(
            relaxed
        )
        if self.l10n_latam_country_code == "DO" and self.l10n_latam_use_documents:
            where_string = where_string.replace("journal_id = %(journal_id)s AND", "")
            where_string += (
                " AND l10n_latam_document_type_id = %(l10n_latam_document_type_id)s AND "
                "company_id = %(company_id)s"
            )
            param["company_id"] = self.company_id.id or False
            param["l10n_latam_document_type_id"] = (
                self.l10n_latam_document_type_id.id or 0
            )
        return where_string, param

    def _get_name_invoice_report(self):
        self.ensure_one()
        if self.l10n_latam_use_documents and self.l10n_latam_country_code == "DO":
            return "l10n_do_accounting.report_invoice_document_inherited"
        return super()._get_name_invoice_report()

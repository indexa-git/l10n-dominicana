from werkzeug import urls

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, AccessError


class AccountMove(models.Model):
    _inherit = "account.move"

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

    ncf_expiration_date = fields.Date(
        string="Valid until",
        store=True,
    )  # TODO: forward-port this field using l10n_do prefix
    is_debit_note = fields.Boolean()

    # DO NOT FORWARD PORT
    cancellation_type = fields.Selection(
        selection="_get_l10n_do_cancellation_type",
        string="Cancellation Type (deprecated)",
        copy=False,
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
    is_l10n_do_internal_sequence = fields.Boolean(
        string="Is internal sequence",
        compute="_compute_l10n_latam_document_type",
        store=True,
    )
    l10n_do_ecf_edi_file = fields.Binary("ECF XML File", copy=False, readonly=True)
    l10n_do_ecf_edi_file_name = fields.Char(
        "ECF XML File Name", copy=False, readonly=True
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
                and invoice.l10n_latam_document_type_id.l10n_do_ncf_type
                and invoice.l10n_latam_document_type_id.l10n_do_ncf_type[:2] == "e-"
            )

    @api.depends(
        "l10n_latam_available_document_type_ids", "type", "l10n_latam_document_type_id"
    )
    @api.depends_context("internal_type")
    def _compute_l10n_latam_document_type(self):
        super(AccountMove, self)._compute_l10n_latam_document_type()

        for invoice in self:
            invoice.is_l10n_do_internal_sequence = invoice.type in (
                "out_invoice",
                "out_refund",
            ) or invoice.l10n_latam_document_type_id.l10n_do_ncf_type in (
                "minor",
                "informal",
                "exterior",
                "e-minor",
                "e-informal",
                "e-exterior",
            )

    @api.depends("company_id", "company_id.l10n_do_ecf_issuer")
    def _compute_company_in_contingency(self):
        for invoice in self:
            ecf_invoices = self.search(
                [
                    ("is_ecf_invoice", "=", True),
                    ("is_l10n_do_internal_sequence", "=", True),
                ],
                limit=1,
            )
            invoice.l10n_do_company_in_contingency = bool(
                ecf_invoices and not invoice.company_id.l10n_do_ecf_issuer
            )

    @api.depends("l10n_do_ecf_security_code", "l10n_do_ecf_sign_date", "invoice_date")
    @api.depends_context("l10n_do_ecf_service_env")
    def _compute_l10n_do_electronic_stamp(self):

        l10n_do_ecf_invoice = self.filtered(
            lambda i: i.is_ecf_invoice
            and i.is_l10n_do_internal_sequence
            and i.l10n_do_ecf_security_code
        )

        for invoice in l10n_do_ecf_invoice:

            ecf_service_env = self.env.context.get("l10n_do_ecf_service_env", "CerteCF")
            doc_code_prefix = invoice.l10n_latam_document_type_id.doc_code_prefix
            is_rfc = (  # Es un Resumen Factura Consumo
                doc_code_prefix == "E32" and invoice.amount_total_signed < 250000
            )

            qr_string = "https://%s.dgii.gov.do/%s/ConsultaTimbre%s?" % (
                "fc" if is_rfc else "ecf",
                ecf_service_env,
                "FC" if is_rfc else "",
            )
            qr_string += "RncEmisor=%s&" % invoice.company_id.vat or ""
            if not is_rfc:
                qr_string += (
                    "RncComprador=%s&" % invoice.commercial_partner_id.vat
                    if invoice.l10n_latam_document_type_id.doc_code_prefix[1:]
                    not in ("43", "47")
                    else ""
                )
            qr_string += "ENCF=%s&" % invoice.ref or ""
            if not is_rfc:
                qr_string += "FechaEmision=%s&" % (
                    invoice.invoice_date or fields.Date.today()
                ).strftime("%d-%m-%Y")
            qr_string += "MontoTotal=%s&" % (
                "%f" % sum(invoice.line_ids.mapped("credit"))
            ).rstrip("0").rstrip(".")
            if not is_rfc:
                qr_string += "FechaFirma=%s&" % invoice.l10n_do_ecf_sign_date.strftime(
                    "%d-%m-%Y%%20%H:%M:%S"
                )

            qr_string += "CodigoSeguridad=%s" % invoice.l10n_do_ecf_security_code or ""

            invoice.l10n_do_electronic_stamp = urls.url_quote_plus(qr_string)

        (self - l10n_do_ecf_invoice).l10n_do_electronic_stamp = False

    @api.constrains("name", "journal_id", "state", "ref")
    def _check_unique_sequence_number(self):
        l10n_do_invoices = self.filtered(
            lambda inv: inv.l10n_latam_use_documents
            and inv.l10n_latam_country_code == "DO"
            and inv.is_sale_document()
            and inv.state == "posted"
        )
        if l10n_do_invoices:
            self.flush()
            self._cr.execute(
                """
                SELECT move2.id
                FROM account_move move
                INNER JOIN account_move move2 ON
                    move2.ref = move.ref
                    AND move2.company_id = move.company_id
                    AND move2.type = move.type
                    AND move2.id != move.id
                WHERE move.id IN %s AND move2.state = 'posted'
            """,
                [tuple(l10n_do_invoices.ids)],
            )
            res = self._cr.fetchone()
            if res:
                raise ValidationError(
                    _("There is already a sale invoice with fiscal number %s")
                    % self.ref
                )

        super(AccountMove, (self - l10n_do_invoices))._check_unique_sequence_number()

    def button_cancel(self):

        fiscal_invoice = self.filtered(
            lambda inv: inv.l10n_latam_country_code == "DO"
            and self.type[-6:] in ("nvoice", "refund")
            and inv.l10n_latam_use_documents
            and not inv.is_ecf_invoice
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
            and self.type[-6:] in ("nvoice", "refund")
        )
        if fiscal_invoice and not self.env.user.has_group(
            "l10n_do_accounting.group_l10n_do_fiscal_credit_note"
        ):
            raise AccessError(_("You are not allowed to issue Fiscal Credit Notes"))

        return super(AccountMove, self).action_reverse()

    @api.depends("ref")
    def _compute_l10n_latam_document_number(self):
        l10n_do_recs = self.filtered(lambda x: x.l10n_latam_country_code == "DO")
        for rec in l10n_do_recs:
            rec.l10n_latam_document_number = rec.ref
        remaining = self - l10n_do_recs
        remaining.l10n_latam_document_number = False
        super(AccountMove, remaining)._compute_l10n_latam_document_number()

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
        if not (
            self.journal_id.l10n_latam_use_documents
            and self.journal_id.company_id.country_id == self.env.ref("base.do")
        ):
            return super()._get_l10n_latam_documents_domain()

        internal_types = ["debit_note"]
        if self.type in ["out_refund", "in_refund"]:
            internal_types.append("credit_note")
        else:
            internal_types.append("invoice")

        domain = [
            ("internal_type", "in", internal_types),
            ("country_id", "=", self.company_id.country_id.id),
        ]
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

    def _get_document_type_sequence(self):
        """ Return the match sequences for the given journal and invoice """
        self.ensure_one()
        if (
            self.journal_id.l10n_latam_use_documents
            and self.l10n_latam_country_code == "DO"
        ):
            res = self.journal_id.l10n_do_sequence_ids.filtered(
                lambda x: x.l10n_latam_document_type_id
                == self.l10n_latam_document_type_id
            )
            return res
        return super()._get_document_type_sequence()

    @api.constrains("type", "l10n_latam_document_type_id")
    def _check_invoice_type_document_type(self):
        l10n_do_invoices = self.filtered(
            lambda inv: inv.l10n_latam_country_code == "DO"
            and inv.l10n_latam_use_documents
            and inv.l10n_latam_document_type_id
        )
        for rec in l10n_do_invoices:
            has_vat = bool(rec.partner_id.vat and bool(rec.partner_id.vat.strip()))
            l10n_latam_document_type = rec.l10n_latam_document_type_id
            if not has_vat and l10n_latam_document_type.is_vat_required:
                raise ValidationError(
                    _(
                        "A VAT is mandatory for this type of NCF. "
                        "Please set the current VAT of this client"
                    )
                )

            elif rec.type in ("out_invoice", "out_refund"):
                if (
                    rec.amount_untaxed_signed >= 250000
                    and l10n_latam_document_type.l10n_do_ncf_type[-7:] != "special"
                    and not has_vat
                ):
                    raise UserError(
                        _(
                            "If the invoice amount is greater than RD$250,000.00 "
                            "the customer should have a VAT to validate the invoice"
                        )
                    )

        super(AccountMove, self - l10n_do_invoices)._check_invoice_type_document_type()

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if (
            self.company_id.country_id == self.env.ref("base.do")
            and self.l10n_latam_document_type_id
            and self.type == "in_invoice"
            and self.partner_id
        ):
            self.l10n_do_expense_type = (
                self.partner_id.l10n_do_expense_type
                if not self.l10n_do_expense_type
                else self.l10n_do_expense_type
            )

        return super(AccountMove, self)._onchange_partner_id()

    def _reverse_move_vals(self, default_values, cancel=True):

        res = super(AccountMove, self)._reverse_move_vals(
            default_values=default_values, cancel=cancel
        )
        if self.l10n_latam_country_code != "DO":
            return res

        res["l10n_do_origin_ncf"] = self.l10n_latam_document_number
        res["l10n_do_ecf_modification_code"] = self.env.context.get(
            "l10n_do_ecf_modification_code"
        )
        res["is_l10n_do_internal_sequence"] = self.is_sale_document()
        return res

    def _move_autocomplete_invoice_lines_create(self, vals_list):

        ctx = self.env.context
        refund_type = ctx.get("refund_type")
        if refund_type and refund_type in ("percentage", "fixed_amount"):
            for vals in vals_list:
                del vals["line_ids"]
                origin_invoice_id = self.browse(self.env.context.get("active_ids"))
                price_unit = (
                    ctx.get("amount")
                    if refund_type == "fixed_amount"
                    else origin_invoice_id.amount_untaxed
                    * (ctx.get("percentage") / 100)
                )
                vals["invoice_line_ids"] = [
                    (
                        0,
                        0,
                        {
                            "name": ctx.get("reason") or _("Refund"),
                            "price_unit": price_unit,
                            "quantity": 1,
                        },
                    )
                ]

        return super(AccountMove, self)._move_autocomplete_invoice_lines_create(
            vals_list
        )

    @api.constrains("name", "partner_id", "company_id")
    def _check_unique_vendor_number(self):

        l10n_do_invoice = self.filtered(
            lambda inv: inv.l10n_latam_country_code == "DO"
            and inv.l10n_latam_use_documents
            and inv.is_purchase_document()
            and inv.l10n_latam_document_number
        )

        for rec in l10n_do_invoice:
            domain = [
                ("type", "=", rec.type),
                ("ref", "=", rec.ref),
                ("company_id", "=", rec.company_id.id),
                ("id", "!=", rec.id),
                ("commercial_partner_id", "=", rec.commercial_partner_id.id),
            ]
            if rec.search(domain):
                raise ValidationError(
                    _("Vendor bill NCF must be unique per vendor and company.")
                )
        return super(AccountMove, self - l10n_do_invoice)._check_unique_vendor_number()

    def post(self):

        res = super(AccountMove, self).post()

        l10n_do_invoices = self.filtered(
            lambda inv: inv.company_id.country_id == self.env.ref("base.do")
            and inv.l10n_latam_use_documents
        )

        for invoice in l10n_do_invoices.filtered(
            lambda inv: inv.l10n_latam_sequence_id
        ):
            invoice.ncf_expiration_date = invoice.l10n_latam_sequence_id.expiration_date

        non_payer_type_invoices = l10n_do_invoices.filtered(
            lambda inv: not inv.partner_id.l10n_do_dgii_tax_payer_type
        )
        if non_payer_type_invoices:
            raise ValidationError(_("Fiscal invoices require partner fiscal type"))

        return res

    @api.model
    def new(self, values={}, origin=None, ref=None):
        if (
            self.l10n_latam_use_documents
            and self.is_ecf_invoice
            and values.get("type") in ("out_refund", "in_refund")
        ):
            values["l10n_latam_document_type_id"] = self.env.ref(
                "l10n_do_accounting.ecf_credit_note_client"
            ).id

        return super(AccountMove, self).new(values, origin, ref)

    def init(self):  # DO NOT FORWARD PORT
        cancelled_invoices = self.search(
            [
                ("state", "=", "cancel"),
                ("l10n_latam_use_documents", "=", True),
                ("cancellation_type", "!=", False),
                ("l10n_do_cancellation_type", "=", False),
            ]
        )
        for invoice in cancelled_invoices:
            invoice.l10n_do_cancellation_type = invoice.cancellation_type

    def unlink(self):
        if self.filtered(
            lambda inv: inv.is_purchase_document()
            and inv.l10n_latam_country_code == "DO"
            and inv.l10n_latam_use_documents
            and inv.name != "/"  # have been posted before
        ):
            raise UserError(
                _("You cannot delete fiscal invoice which have been posted before")
            )
        return super(AccountMove, self).unlink()

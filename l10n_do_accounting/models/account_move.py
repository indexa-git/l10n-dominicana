import re
from werkzeug import urls

from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.exceptions import ValidationError, UserError, AccessError
from odoo.tools.sql import column_exists, create_column, drop_index, index_exists


class AccountMove(models.Model):
    _inherit = "account.move"
    _rec_names_search = ["l10n_do_fiscal_number"]

    _l10n_do_sequence_field = "l10n_do_fiscal_number"
    _l10n_do_sequence_fixed_regex = r"^(?P<prefix1>.*?)(?P<seq>\d{0,8})$"

    def _get_l10n_do_cancellation_type(self):
        """Return the list of cancellation types required by DGII."""
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
        """Return the list of e-CF modification codes required by DGII."""
        return [
            ("1", _("01 - Total Cancellation")),
            ("2", _("02 - Text Correction")),
            ("3", _("03 - Amount correction")),
            ("4", _("04 - NCF replacement issued in contingency")),
            ("5", _("05 - Reference Electronic Consumer Invoice")),
        ]

    def _get_l10n_do_income_type(self):
        """Return the list of income types required by DGII."""
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

    l10n_do_ncf_expiration_date = fields.Date(
        string="Valid until",
    )
    is_ecf_invoice = fields.Boolean(
        compute="_compute_is_ecf_invoice",
        store=True,
    )
    l10n_do_ecf_modification_code = fields.Selection(
        selection="_get_l10n_do_ecf_modification_code",
        string="e-CF Modification Code",
        copy=False,
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
    l10n_do_sequence_prefix = fields.Char(compute="_compute_split_sequence", store=True)
    l10n_do_sequence_number = fields.Integer(
        compute="_compute_split_sequence", store=True
    )
    l10n_do_enable_first_sequence = fields.Boolean(
        string="Enable first fiscal sequence",
        compute="_compute_l10n_do_enable_first_sequence",
        help="Technical field that compute if internal generated fiscal sequence "
        "is enabled to be set manually.",
    )
    l10n_do_fiscal_number = fields.Char(
        "Fiscal Number",
        index="trigram",
        tracking=True,
        copy=False,
        help="Stored field equivalent of l10n_latam_document number",
    )
    l10n_do_ecf_edi_file = fields.Binary("ECF XML File", copy=False, readonly=True)
    l10n_do_ecf_edi_file_name = fields.Char(
        "ECF XML File Name", copy=False, readonly=True
    )
    l10n_latam_manual_document_number = fields.Boolean(store=True)
    l10n_do_show_expiration_date_msg = fields.Boolean(
        "Show Expiration Date Message",
        compute="_compute_l10n_do_show_expiration_date_msg",
        help="Technical field to hide/show message on invoice header that indicate fiscal number must be input "
        "manually because a new expiration date was set on journal",
    )

    _sql_constraints = [
        (
            "unique_l10n_do_fiscal_number_sales",
            "",
            "Another document with the same fiscal number already exists.",
        ),
        (
            "unique_l10n_do_fiscal_number_purchase_manual",
            "",
            "Another document for the same partner with the same fiscal number already exists.",
        ),
        (
            "unique_l10n_do_fiscal_number_purchase_internal",
            "",
            "Another document for the same partner with the same fiscal number already exists.",
        ),
    ]

    def _auto_init(self):
        if not index_exists(
            self.env.cr, "account_move_unique_l10n_do_fiscal_number_sales"
        ):
            drop_index(
                self.env.cr,
                "account_move_unique_l10n_do_fiscal_number_purchase_manual",
                self._table,
            )
            drop_index(
                self.env.cr,
                "account_move_unique_l10n_do_fiscal_number_purchase_internal",
                self._table,
            )

            if not column_exists(self.env.cr, "account_move", "l10n_do_fiscal_number"):
                create_column(
                    self.env.cr, "account_move", "l10n_do_fiscal_number", "varchar"
                )
            if not column_exists(self.env.cr, "account_move", "l10n_latam_manual_document_number"):
                create_column(
                    self.env.cr, "account_move", "l10n_latam_manual_document_number", "varchar"
                )

            self.env.cr.execute(
                """
                CREATE UNIQUE INDEX account_move_unique_l10n_do_fiscal_number_sales
                ON account_move(l10n_do_fiscal_number, company_id)
                WHERE (l10n_latam_document_type_id IS NOT NULL
                AND move_type NOT IN ('in_invoice', 'in_refund'))
                AND l10n_do_fiscal_number <> '';
                
                CREATE UNIQUE INDEX account_move_unique_l10n_do_fiscal_number_purchase_manual
                ON account_move(l10n_do_fiscal_number, commercial_partner_id, company_id)
                WHERE (l10n_latam_document_type_id IS NOT NULL AND move_type IN ('in_invoice', 'in_refund')
                AND l10n_latam_manual_document_number = 't')
                AND l10n_do_fiscal_number <> '';
                
                CREATE UNIQUE INDEX account_move_unique_l10n_do_fiscal_number_purchase_internal
                ON account_move(l10n_do_fiscal_number, company_id)
                WHERE (l10n_latam_document_type_id IS NOT NULL AND move_type IN ('in_invoice', 'in_refund', 'in_receipt')
                AND l10n_latam_manual_document_number = 'f')
                AND l10n_do_fiscal_number <> '';
            """
            )
        return super()._auto_init()

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        if name:
            domain = expression.AND([[
                "|",
                ("name", operator, name),
                ("l10n_do_fiscal_number", operator, name),
            ], domain])
        return super()._name_search(name, domain, operator, limit, order)

    def _l10n_do_is_new_expiration_date(self):
        self.ensure_one()
        last_invoice = self.search(
            [
                ("company_id", "=", self.company_id.id),
                ("move_type", "=", self.move_type),
                (
                    "l10n_latam_document_type_id",
                    "=",
                    self.l10n_latam_document_type_id.id,
                ),
                ("posted_before", "=", True),
                ("id", "!=", self.id or self._origin.id),
                ("l10n_do_ncf_expiration_date", "!=", False),
            ],
            order="invoice_date desc, id desc",
            limit=1,
        )
        if not last_invoice:
            return False

        return (
            last_invoice.l10n_do_ncf_expiration_date < self.l10n_do_ncf_expiration_date
        )

    @api.depends("l10n_do_ncf_expiration_date", "journal_id")
    def _compute_l10n_do_show_expiration_date_msg(self):
        l10n_do_internal_invoices = self.filtered(
            lambda inv: inv.l10n_latam_use_documents
            and inv.l10n_latam_document_type_id
            and inv.country_code == "DO"
            and not inv.l10n_latam_manual_document_number
            and inv.l10n_do_ncf_expiration_date
        )
        for invoice in l10n_do_internal_invoices:
            invoice.l10n_do_show_expiration_date_msg = (
                invoice._l10n_do_is_new_expiration_date()
            )

        (self - l10n_do_internal_invoices).l10n_do_show_expiration_date_msg = False

    @api.depends(
        "journal_id.l10n_latam_use_documents",
        "l10n_latam_manual_document_number",
        "l10n_latam_document_type_id",
        "company_id",
    )
    def _compute_l10n_do_enable_first_sequence(self):
        """
        Enable first fiscal sequence manual input on internal generated documents
        if no invoice of same document type was posted before
        """
        l10n_do_internal_invoices = self.filtered(
            lambda inv: inv.l10n_latam_use_documents
            and inv.l10n_latam_document_type_id
            and inv.country_code == "DO"
            and not inv.l10n_latam_manual_document_number
        )
        for invoice in l10n_do_internal_invoices:
            invoice.l10n_do_enable_first_sequence = (
                not bool(
                    self.search_count(
                        [
                            ("company_id", "=", invoice.company_id.id),
                            ("move_type", "=", invoice.move_type),
                            (
                                "l10n_latam_document_type_id",
                                "=",
                                invoice.l10n_latam_document_type_id.id,
                            ),
                            ("posted_before", "=", True),
                            ("id", "!=", invoice.id or invoice._origin.id),
                        ],
                    )
                )
                or invoice.l10n_do_show_expiration_date_msg
            )

        (self - l10n_do_internal_invoices).l10n_do_enable_first_sequence = False

    def _get_l10n_do_amounts(self):
        """
        Method used to prepare dominican fiscal invoices amounts data. Widely used
        on reports and electronic invoicing.
        """
        self.ensure_one()

        return self.line_ids.filtered(
            lambda line: line.currency_id == self.currency_id
        )._get_l10n_do_line_amounts()

    @api.depends(
        "company_id",
        "l10n_latam_document_type_id",
    )
    def _compute_is_ecf_invoice(self):
        for invoice in self.filtered(lambda inv: inv.state == "draft"):
            invoice.is_ecf_invoice = (
                invoice.company_id.country_id
                and invoice.country_code == "DO"
                and invoice.l10n_latam_document_type_id
                and invoice.l10n_latam_document_type_id.l10n_do_ncf_type
                and invoice.l10n_latam_document_type_id.l10n_do_ncf_type[:2] == "e-"
            )

    @api.depends("company_id", "company_id.l10n_do_ecf_issuer")
    def _compute_company_in_contingency(self):
        ecf_invoices = self.search(
            [
                ("is_ecf_invoice", "=", True),
            ],
            limit=1,
        ).filtered(lambda i: not i.l10n_latam_manual_document_number)

        # first set all invoices l10n_do_company_in_contingency = False
        self.write({"l10n_do_company_in_contingency": False})

        # then get draft invoices and do the thing
        for invoice in self.filtered(lambda inv: inv.state == "draft"):
            invoice.l10n_do_company_in_contingency = bool(
                ecf_invoices and not invoice.company_id.l10n_do_ecf_issuer
            )

    @api.depends("l10n_do_ecf_security_code", "l10n_do_ecf_sign_date", "invoice_date")
    def _compute_l10n_do_electronic_stamp(self):
        l10n_do_ecf_invoice = self.filtered(
            lambda i: i.is_ecf_invoice
            and not i.l10n_latam_manual_document_number
            and i.l10n_do_ecf_security_code
            and i.state == "posted"
        )

        for invoice in l10n_do_ecf_invoice:
            if hasattr(invoice.company_id, "l10n_do_ecf_service_env"):
                ecf_service_env = invoice.company_id.l10n_do_ecf_service_env
            else:
                ecf_service_env = "TesteCF"

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
            qr_string += "ENCF=%s&" % invoice.l10n_do_fiscal_number or ""
            if not is_rfc:
                qr_string += "FechaEmision=%s&" % (
                    invoice.invoice_date or fields.Date.today()
                ).strftime("%d-%m-%Y")

            total_field = "l10n_do_invoice_total"
            if invoice.currency_id != invoice.company_id.currency_id:
                total_field += "_currency"
            l10n_do_total = invoice._get_l10n_do_amounts()[total_field]

            qr_string += "MontoTotal=%s&" % ("%f" % l10n_do_total).rstrip("0").rstrip(
                "."
            )
            if not is_rfc:
                qr_string += "FechaFirma=%s&" % invoice.l10n_do_ecf_sign_date.strftime(
                    "%d-%m-%Y %H:%M:%S"
                )

            special_chars = " !#$&'()*+,/:;=?@[]\"-.<>\\^_`"
            security_code = "".join(
                c.replace(c, "%" + c.encode("utf-8").hex()).upper()
                if c in special_chars
                else c
                for c in invoice.l10n_do_ecf_security_code or ""
            )
            qr_string += "CodigoSeguridad=%s" % security_code

            invoice.l10n_do_electronic_stamp = urls.url_quote_plus(qr_string, safe="%")

        (self - l10n_do_ecf_invoice).l10n_do_electronic_stamp = False

    @api.constrains(
        "l10n_do_fiscal_number", "partner_id", "company_id", "posted_before"
    )
    def _l10n_do_check_unique_vendor_number(self):
        for rec in self.filtered(
            lambda inv: inv.l10n_do_fiscal_number
            and inv.country_code == "DO"
            and inv.l10n_latam_use_documents
            and inv.is_purchase_document()
            and inv.commercial_partner_id
        ):
            domain = [
                ("move_type", "=", rec.move_type),
                ("l10n_do_fiscal_number", "=", rec.l10n_do_fiscal_number),
                ("company_id", "=", rec.company_id.id),
                ("id", "!=", rec.id),
                ("commercial_partner_id", "=", rec.commercial_partner_id.id),
                ("state", "!=", "cancel"),
            ]
            if rec.search_count(domain):
                raise ValidationError(
                    _(
                        "Vendor bill Fiscal Number must be unique per vendor and company."
                    )
                )

    @api.depends("l10n_do_fiscal_number")
    def _compute_l10n_latam_document_number(self):
        l10n_do_recs = self.filtered(
            lambda x: x.country_code == "DO" and x.l10n_latam_use_documents
        )
        for rec in l10n_do_recs:
            rec.l10n_latam_document_number = rec.l10n_do_fiscal_number

        super(AccountMove, self - l10n_do_recs)._compute_l10n_latam_document_number()

    def button_cancel(self):
        fiscal_invoice = self.filtered(
            lambda inv: inv.country_code == "DO"
            and self.move_type[-6:] in ("nvoice", "refund")
            and inv.l10n_latam_use_documents
        )
        not_ecf_fiscal_invoice = fiscal_invoice.filtered(lambda i: not i.is_ecf_invoice)

        if len(fiscal_invoice) > 1:
            raise ValidationError(
                _("You cannot cancel multiple fiscal invoices at a time.")
            )

        if not_ecf_fiscal_invoice and not self.env.user.has_group(
            "l10n_do_accounting.group_l10n_do_fiscal_invoice_cancel"
        ):
            raise AccessError(_("You are not allowed to cancel Fiscal Invoices"))

        if fiscal_invoice and not fiscal_invoice.posted_before:
            raise ValidationError(
                _(
                    "You cannot cancel a fiscal document that has not been posted before."
                )
            )

        if not_ecf_fiscal_invoice and not self.env.context.get(
            "skip_cancel_wizard", False
        ):
            action = (
                self.env.ref("l10n_do_accounting.action_account_move_cancel")
                .sudo()
                .read()[0]
            )
            action["context"] = {"default_move_id": fiscal_invoice.id}
            return action

        if fiscal_invoice:
            fiscal_invoice.button_draft()

        return super(AccountMove, self).button_cancel()

    def action_reverse(self):
        fiscal_invoice = self.filtered(
            lambda inv: inv.country_code == "DO"
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
                rec.l10n_do_fiscal_number = ""
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
                rec.l10n_do_fiscal_number = document_number
        super(
            AccountMove, self.filtered(lambda m: m.country_code != "DO")
        )._inverse_l10n_latam_document_number()

    def _get_l10n_latam_documents_domain(self):
        self.ensure_one()
        if not (
            self.journal_id.l10n_latam_use_documents
            and self.journal_id.company_id.country_id == self.env.ref("base.do")
        ):
            return super()._get_l10n_latam_documents_domain()

        internal_types = ["debit_note"]
        if self.move_type in ["out_refund", "in_refund"]:
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

    @api.constrains("move_type", "l10n_latam_document_type_id")
    def _check_invoice_type_document_type(self):
        l10n_do_invoices = self.filtered(
            lambda inv: inv.country_code == "DO"
            and inv.l10n_latam_use_documents
            and inv.l10n_latam_document_type_id
            and inv.state == "posted"
        )
        for rec in l10n_do_invoices:
            has_vat = bool(rec.partner_id.vat and bool(rec.partner_id.vat.strip()))
            l10n_latam_document_type = rec.l10n_latam_document_type_id
            if not has_vat and (
                rec.amount_untaxed_signed >= 250000
                or (
                    l10n_latam_document_type.is_vat_required
                    and rec.commercial_partner_id.l10n_do_dgii_tax_payer_type
                    != "non_payer"
                )
            ):
                raise ValidationError(
                    _(
                        "A VAT is mandatory for this type of NCF. "
                        "Please set the current VAT of this client"
                    )
                )
        super(AccountMove, self - l10n_do_invoices)._check_invoice_type_document_type()

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
        if self.country_code != "DO":
            return res

        if self.country_code == "DO":
            res["l10n_do_origin_ncf"] = self.l10n_do_fiscal_number or self.ref
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

    @api.depends("l10n_latam_document_type_id", "journal_id")
    def _compute_l10n_latam_manual_document_number(self):
        l10n_do_recs_with_journal_id = self.filtered(
            lambda x: x.journal_id
            and x.journal_id.l10n_latam_use_documents
            and x.l10n_latam_document_type_id
            and x.country_code == "DO"
        )
        for move in l10n_do_recs_with_journal_id:
            move.l10n_latam_manual_document_number = (
                move._is_l10n_do_manual_document_number()
            )

            move.l10n_do_ncf_expiration_date = (
                move.journal_id.l10n_do_document_type_ids.filtered(
                    lambda doc: doc.l10n_latam_document_type_id
                    == move.l10n_latam_document_type_id
                ).l10n_do_ncf_expiration_date
            )

        super(
            AccountMove, self - l10n_do_recs_with_journal_id
        )._compute_l10n_latam_manual_document_number()

    def _is_l10n_do_manual_document_number(self):
        self.ensure_one()

        if self.reversed_entry_id:
            return self.reversed_entry_id.l10n_latam_manual_document_number

        return self.move_type in (
            "in_invoice",
            "in_refund",
        ) and self.l10n_latam_document_type_id.l10n_do_ncf_type not in (
            "minor",
            "e-minor",
            "informal",
            "e-informal",
            "exterior",
            "e-exterior",
        )

    def _get_debit_line_tax(self, debit_date):
        if self.move_type == "out_invoice":
            return (
                self.company_id.account_sale_tax_id
                or self.env.ref("account.%s_tax_18_sale" % self.company_id.id)
                if (debit_date - self.invoice_date).days <= 30
                and self.partner_id.l10n_do_dgii_tax_payer_type != "special"
                else self.env.ref("account.%s_tax_0_sale" % self.company_id.id) or False
            )
        else:
            return self.company_id.account_purchase_tax_id or self.env.ref(
                "account.%s_tax_0_purch" % self.company_id.id
            )

    def _post(self, soft=True):
        res = super()._post(soft)

        l10n_do_invoices = self.filtered(
            lambda inv: inv.company_id.country_id == self.env.ref("base.do")
            and inv.l10n_latam_use_documents
        )

        for invoice in l10n_do_invoices.filtered(
            lambda inv: inv.l10n_latam_document_type_id
        ):
            if not invoice.amount_total:
                raise UserError(_("Fiscal invoice cannot be posted with amount zero."))

        non_payer_type_invoices = l10n_do_invoices.filtered(
            lambda inv: not inv.partner_id.l10n_do_dgii_tax_payer_type
        )
        if non_payer_type_invoices:
            raise ValidationError(_("Fiscal invoices require partner fiscal type"))

        return res

    def _l10n_do_get_formatted_sequence(self):
        self.ensure_one()
        if not self._context.get("is_l10n_do_seq", False):
            starting_sequence = "%s/%04d/0000" % (
                self.journal_id.code,
                self.date.year,
            )
            if self.journal_id.refund_sequence and self.move_type in (
                "out_refund",
                "in_refund",
            ):
                starting_sequence = "R" + starting_sequence
            return starting_sequence

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
            and self.country_code == "DO"
        ):
            return self._l10n_do_get_formatted_sequence()

        return super()._get_starting_sequence()

    def _get_last_sequence_domain(self, relaxed=False):
        where_string, param = super(AccountMove, self)._get_last_sequence_domain(
            relaxed
        )

        if self.l10n_latam_use_documents and self.country_code == "DO":
            where_string = where_string.replace(
                "AND sequence_prefix !~ %(anti_regex)s ", ""
            )
        if self._context.get("is_l10n_do_seq", False):
            where_string = where_string.replace("journal_id = %(journal_id)s AND", "")
            where_string += (
                " AND l10n_latam_document_type_id = %(l10n_latam_document_type_id)s AND"
                " company_id = %(company_id)s AND l10n_do_sequence_prefix != ''"
                " AND l10n_do_sequence_prefix IS NOT NULL"
            )
            if (
                not self.l10n_latam_manual_document_number
                and self.move_type != "in_refund"
            ):
                where_string += " AND move_type = %(move_type)s"
                param["move_type"] = self.move_type
            else:
                where_string += " AND l10n_latam_manual_document_number = 'f'"

            param["company_id"] = self.company_id.id or False
            param["l10n_latam_document_type_id"] = (
                self.l10n_latam_document_type_id.id or 0
            )
        return where_string, param

    @api.depends(lambda self: [self._l10n_do_sequence_field])
    def _compute_split_sequence(self):
        super(AccountMove, self)._compute_split_sequence()
        for record in self:
            sequence = record[record._l10n_do_sequence_field] or ""
            regex = re.sub(
                r"\?P<\w+>",
                "?:",
                record._l10n_do_sequence_fixed_regex.replace(r"?P<seq>", ""),
            )
            matching = re.match(regex, sequence)
            record.l10n_do_sequence_prefix = sequence[:3]
            record.l10n_do_sequence_number = int(matching.group(1) or 0)

    def _get_last_sequence(self, relaxed=False, with_prefix=None):
        if not self._context.get("is_l10n_do_seq", False):
            return super(AccountMove, self)._get_last_sequence(
                relaxed=relaxed, with_prefix=with_prefix
            )

        self.ensure_one()
        if (
            self._l10n_do_sequence_field not in self._fields
            or not self._fields[self._l10n_do_sequence_field].store
        ):
            raise ValidationError(
                _("%s is not a stored field", self._l10n_do_sequence_field)
            )
        where_string, param = self._get_last_sequence_domain(relaxed)
        if self.id or self.id.origin:
            where_string += " AND id != %(id)s "
            param["id"] = self.id or self.id.origin

        query = """
            UPDATE {table} SET write_date = write_date WHERE id = (
                SELECT id FROM {table}
                {where_string}
                AND l10n_do_sequence_prefix = (
                SELECT l10n_do_sequence_prefix
                FROM {table} {where_string}
                ORDER BY id DESC LIMIT 1)
                ORDER BY l10n_do_sequence_number DESC
                LIMIT 1
            )
            RETURNING {field};
        """.format(
            table=self._table,
            where_string=where_string,
            field=self._l10n_do_sequence_field,
        )

        self.flush_model(
            [
                self._l10n_do_sequence_field,
                "l10n_do_sequence_number",
                "l10n_do_sequence_prefix",
            ]
        )
        self.env.cr.execute(query, param)
        return (self.env.cr.fetchone() or [None])[0]

    def _get_sequence_format_param(self, previous):
        if not self._context.get("is_l10n_do_seq", False):
            return super(AccountMove, self)._get_sequence_format_param(previous)

        regex = self._l10n_do_sequence_fixed_regex

        format_values = re.match(regex, previous).groupdict()
        format_values["seq_length"] = len(format_values["seq"])
        format_values["seq"] = int(format_values.get("seq") or 0)

        placeholders = re.findall(r"(prefix\d|seq\d?)", regex)
        format = "".join(
            "{seq:0{seq_length}d}" if s == "seq" else "{%s}" % s for s in placeholders
        )
        return format, format_values

    def _set_next_sequence(self):
        self.ensure_one()

        if not self._context.get("is_l10n_do_seq", False):
            return super(AccountMove, self)._set_next_sequence()

        last_sequence = self._get_last_sequence()
        new = not last_sequence
        if new:
            last_sequence = (
                self._get_last_sequence(relaxed=True) or self._get_starting_sequence()
            )

        format, format_values = self._get_sequence_format_param(last_sequence)
        if new:
            format_values["seq"] = 0
        format_values["seq"] = format_values["seq"] + 1

        if (
            self.env.context.get("prefetch_seq")
            or self.state != "draft"
            and not self[self._l10n_do_sequence_field]
        ):
            self[
                self._l10n_do_sequence_field
            ] = self.l10n_latam_document_type_id._format_document_number(
                format.format(**format_values)
            )
        self._compute_split_sequence()

    def _get_name_invoice_report(self):
        self.ensure_one()
        if self.l10n_latam_use_documents and self.country_code == "DO":
            return "l10n_do_accounting.report_invoice_document_inherited"
        return super()._get_name_invoice_report()

    # TODO: handle l10n_latam_invoice_document _compute_name() inheritance shit

    def unlink(self):
        if self.filtered(
            lambda inv: inv.is_purchase_document()
            and inv.country_code == "DO"
            and inv.l10n_latam_use_documents
            and inv.posted_before
        ):
            raise UserError(
                _("You cannot delete fiscal invoice which have been posted before")
            )
        return super(AccountMove, self).unlink()

    # Extension of the _deduce_sequence_number_reset function to compute the `name` field according to the invoice
    # date and prevent the `l10n_latam_document_number` field from being reset
    @api.model
    def _deduce_sequence_number_reset(self, name):
        if (
            self.l10n_latam_use_documents
            and self.company_id.country_id.code == "DO"
            and self.posted_before
            and not self._context.get("is_l10n_do_seq", False)
        ):
            return "year"
        elif self._context.get("is_l10n_do_seq", False):
            return "never"
        else:
            "never"
        return super(AccountMove, self)._deduce_sequence_number_reset(name)

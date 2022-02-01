import re
from psycopg2 import sql
from werkzeug import urls

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, AccessError


class AccountMove(models.Model):
    _inherit = "account.move"

    _l10n_do_sequence_field = "l10n_do_fiscal_number"
    _l10n_do_sequence_fixed_regex = r"^(?P<prefix1>.*?)(?P<seq>\d{0,8})$"

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
        index=True,
        copy=False,
        help="Stored field equivalent of l10n_latam_document number",
    )
    l10n_do_ecf_edi_file = fields.Binary("ECF XML File", copy=False, readonly=True)
    l10n_do_ecf_edi_file_name = fields.Char(
        "ECF XML File Name", copy=False, readonly=True
    )
    l10n_latam_manual_document_number = fields.Boolean(store=True)

    def init(self):

        super(AccountMove, self).init()

        if not self._abstract and self._sequence_index:
            index_name = self._table + "_l10n_do_sequence_index"
            self.env.cr.execute(
                "SELECT indexname FROM pg_indexes WHERE indexname = %s", (index_name,)
            )
            if not self.env.cr.fetchone():
                self.env.cr.execute(
                    sql.SQL(
                        """
                        CREATE INDEX {index_name} ON {table}
                        ({sequence_index},
                        l10n_do_sequence_prefix desc,
                        l10n_do_sequence_number desc,
                        {field});
                        CREATE INDEX {index2_name} ON {table}
                        ({sequence_index},
                        id desc,
                        l10n_do_sequence_prefix);
                    """
                    ).format(
                        sequence_index=sql.Identifier(self._sequence_index),
                        index_name=sql.Identifier(index_name),
                        index2_name=sql.Identifier(index_name + "2"),
                        table=sql.Identifier(self._table),
                        field=sql.Identifier(self._l10n_do_sequence_field),
                    )
                )

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
            invoice.l10n_do_enable_first_sequence = not bool(
                self.search_count(
                    [
                        ("company_id", "=", invoice.company_id.id),
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

        (self - l10n_do_internal_invoices).l10n_do_enable_first_sequence = False

    @api.depends(
        "company_id",
        "l10n_latam_document_type_id.l10n_do_ncf_type",
    )
    def _compute_is_ecf_invoice(self):
        for invoice in self:
            invoice.is_ecf_invoice = (
                invoice.company_id.country_id
                and invoice.company_id.country_id.code == "DO"
                and invoice.l10n_latam_document_type_id
                and invoice.l10n_latam_document_type_id.l10n_do_ncf_type
                and invoice.l10n_latam_document_type_id.l10n_do_ncf_type[:2] == "e-"
            )

    @api.depends("company_id", "company_id.l10n_do_ecf_issuer")
    def _compute_company_in_contingency(self):
        for invoice in self:
            ecf_invoices = self.search(
                [("is_ecf_invoice", "=", True)], limit=1
            ).filtered(lambda i: not i.l10n_latam_manual_document_number)
            invoice.l10n_do_company_in_contingency = bool(
                ecf_invoices and not invoice.company_id.l10n_do_ecf_issuer
            )

    @api.depends("l10n_do_ecf_security_code", "l10n_do_ecf_sign_date", "invoice_date")
    @api.depends_context("l10n_do_ecf_service_env")
    def _compute_l10n_do_electronic_stamp(self):

        l10n_do_ecf_invoice = self.filtered(
            lambda i: i.is_ecf_invoice
            and not i.l10n_latam_manual_document_number
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
                    if invoice.l10n_latam_document_type_id.doc_code_prefix[1:] != "43"
                    else invoice.company_id.vat
                )
            qr_string += "ENCF=%s&" % invoice.l10n_do_fiscal_number or ""
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

            special_chars = " !#$&'()*+,/:;=?@[]\"-.<>\\^_`"
            security_code = "".join(
                c.replace(c, "%" + c.encode("utf-8").hex()).upper()
                if c in special_chars
                else c
                for c in invoice.l10n_do_ecf_security_code or ""
            )
            qr_string += "CodigoSeguridad=%s" % security_code

            invoice.l10n_do_electronic_stamp = urls.url_quote_plus(qr_string)

        (self - l10n_do_ecf_invoice).l10n_do_electronic_stamp = False

    @api.constrains("name", "journal_id", "state", "l10n_do_fiscal_number")
    def _check_unique_sequence_number(self):
        l10n_do_invoices = self.filtered(
            lambda inv: inv.l10n_latam_use_documents
            and inv.country_code == "DO"
            and inv.is_sale_document()
            and inv.state == "posted"
        )
        if l10n_do_invoices:
            self.flush(
                ["name", "journal_id", "move_type", "state", "l10n_do_fiscal_number"]
            )
            self._cr.execute(
                """
                SELECT move2.id, move2.l10n_do_fiscal_number
                FROM account_move move
                INNER JOIN account_move move2 ON
                    move2.l10n_do_fiscal_number = move.l10n_do_fiscal_number
                    AND move2.journal_id = move.journal_id
                    AND move2.move_type = move.move_type
                    AND move2.id != move.id
                WHERE move.id IN %s AND move2.state = 'posted'
            """,
                [tuple(l10n_do_invoices.ids)],
            )
            res = self._cr.fetchone()
            if res:
                raise ValidationError(
                    _("There is already a sale invoice with fiscal number %s")
                    % self.l10n_do_fiscal_number
                )

        super(AccountMove, (self - l10n_do_invoices))._check_unique_sequence_number()

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

            elif rec.move_type in ("out_invoice", "out_refund"):
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
                or self.env.ref("l10n_do.tax_18_sale")
                if (debit_date - self.invoice_date).days <= 30
                and self.partner_id.l10n_do_dgii_tax_payer_type != "special"
                else self.env.ref("l10n_do.tax_0_sale") or False
            )
        else:
            return self.company_id.account_purchase_tax_id or self.env.ref(
                "l10n_do.tax_0_purch"
            )

    def _move_autocomplete_invoice_lines_create(self, vals_list):

        ctx = self.env.context
        refund_type = ctx.get("refund_type")
        refund_debit_type = ctx.get("l10n_do_debit_type", refund_type)
        if refund_debit_type and refund_debit_type in ("percentage", "fixed_amount"):
            for vals in vals_list:
                del vals["line_ids"]
                origin_invoice_id = self.browse(self.env.context.get("active_ids"))
                taxes = (
                    [
                        (
                            6,
                            0,
                            [
                                origin_invoice_id._get_debit_line_tax(
                                    vals["invoice_date"]
                                ).id
                            ],
                        )
                    ]
                    if ctx.get("l10n_do_debit_type", False)
                    else [(5, 0)]
                )
                price_unit = (
                    ctx.get("amount")
                    if refund_debit_type == "fixed_amount"
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
                            "tax_ids": taxes,
                        },
                    )
                ]

        return super(AccountMove, self)._move_autocomplete_invoice_lines_create(
            vals_list
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
            invoice.l10n_do_ncf_expiration_date = (
                invoice.l10n_latam_document_type_id.l10n_do_ncf_expiration_date
            )

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
            and self.company_id.country_id.code == "DO"
            and self.l10n_latam_document_type_id
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
                " company_id = %(company_id)s"
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

    def _get_last_sequence(self, relaxed=False):

        if not self._context.get("is_l10n_do_seq", False):
            return super(AccountMove, self)._get_last_sequence(relaxed=relaxed)

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

        self.flush(
            [
                self._l10n_do_sequence_field,
                "l10n_do_sequence_number",
                "l10n_do_sequence_prefix",
            ]
        )
        self.env.cr.execute(query, param)
        return (self.env.cr.fetchone() or [None])[0]

    @api.model
    def new(self, values={}, origin=None, ref=None):
        if (
            self.l10n_latam_use_documents
            and self.is_ecf_invoice
            and values.get("move_type") in ("out_refund", "in_refund")
        ):
            values["l10n_latam_document_type_id"] = self.env.ref(
                "l10n_do_accounting.ecf_credit_note_client"
            ).id

        return super(AccountMove, self).new(values, origin, ref)

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

        if self.state != "draft":
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

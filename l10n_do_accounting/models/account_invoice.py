# TODO: poner authorship en todos los archivos .py (xml tamb?)

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

try:
    from stdnum.do import ncf as ncf_validation
except (ImportError, IOError) as err:
    _logger.debug(err)

ncf_dict = {
    "B01": "fiscal",
    "B02": "consumo",
    "B15": "gov",
    "B14": "especial",
    "B12": "unico",
    "B16": "export",
    "B03": "debit",
    "B04": "credit",
    "B13": "minor",
    "B11": "informal",
    "B17": "exterior",
}


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    fiscal_type_id = fields.Many2one(
        "account.fiscal.type", string="Fiscal Type", index=True,
    )
    fiscal_sequence_id = fields.Many2one(
        "account.fiscal.sequence",
        string="Fiscal Sequence",
        copy=False,
        compute="_compute_fiscal_sequence",
        store=True,
    )
    income_type = fields.Selection(
        [
            ("01", "01 - Ingresos por Operaciones (No Financieros)"),
            ("02", "02 - Ingresos Financieros"),
            ("03", "03 - Ingresos Extraordinarios"),
            ("04", "04 - Ingresos por Arrendamientos"),
            ("05", "05 - Ingresos por Venta de Activo Depreciable"),
            ("06", "06 - Otros Ingresos"),
        ],
        string="Income Type",
        default=lambda self: self._context.get("income_type", "01"),
    )

    expense_type = fields.Selection(
        [
            ("01", "01 - Gastos de Personal"),
            ("02", "02 - Gastos por Trabajo, Suministros y Servicios"),
            ("03", "03 - Arrendamientos"),
            ("04", "04 - Gastos de Activos Fijos"),
            ("05", u"05 - Gastos de Representación"),
            ("06", "06 - Otras Deducciones Admitidas"),
            ("07", "07 - Gastos Financieros"),
            ("08", "08 - Gastos Extraordinarios"),
            ("09", "09 - Compras y Gastos que forman parte del Costo de Venta"),
            ("10", "10 - Adquisiciones de Activos"),
            ("11", "11 - Gastos de Seguros"),
        ],
        string="Cost & Expense Type",
    )

    anulation_type = fields.Selection(
        [
            ("01", "01 - Deterioro de Factura Pre-impresa"),
            ("02", u"02 - Errores de Impresión (Factura Pre-impresa)"),
            ("03", u"03 - Impresión Defectuosa"),
            ("04", u"04 - Corrección de la Información"),
            ("05", "05 - Cambio de Productos"),
            ("06", u"06 - Devolución de Productos"),
            ("07", u"07 - Omisión de Productos"),
            ("08", "08 - Errores en Secuencia de NCF"),
            ("09", "09 - Por Cese de Operaciones"),
            ("10", u"10 - Pérdida o Hurto de Talonarios"),
        ],
        string="Annulment Type",
        copy=False,
    )
    origin_out = fields.Char("Affects",)
    ncf_expiration_date = fields.Date("Valid until", store=True,)
    is_l10n_do_fiscal_invoice = fields.Boolean(
        compute="_compute_is_l10n_do_fiscal_invoice",
        store=True,
        string="Is Fiscal Invoice",
    )
    assigned_sequence = fields.Boolean(related="fiscal_type_id.assigned_sequence",)
    fiscal_sequence_status = fields.Selection(
        [
            ("no_fiscal", "No fiscal"),
            ("fiscal_ok", "Ok"),
            ("almost_no_sequence", "Almost no sequence"),
            ("no_sequence", "Depleted"),
        ],
        compute="_compute_fiscal_sequence_status",
    )
    is_debit_note = fields.Boolean()

    @api.multi
    @api.depends("state", "journal_id")
    def _compute_is_l10n_do_fiscal_invoice(self):
        for inv in self:
            inv.is_l10n_do_fiscal_invoice = inv.journal_id.l10n_do_fiscal_journal

    @api.multi
    @api.depends(
        "journal_id",
        "is_l10n_do_fiscal_invoice",
        "state",
        "fiscal_type_id",
        "date_invoice",
        "type",
        "is_debit_note",
    )
    def _compute_fiscal_sequence(self):
        """ Compute the sequence and fiscal position to be used depending on
            the fiscal type that has been set on the invoice (or partner).
        """
        for inv in self.filtered(lambda i: i.state == "draft"):
            if inv.is_debit_note:
                debit_map = {"in_invoice": "in_debit", "out_invoice": "out_debit"}
                fiscal_type = self.env["account.fiscal.type"].search(
                    [("type", "=", debit_map[inv.type])], limit=1
                )
                inv.fiscal_type_id = fiscal_type.id
            elif inv.type in ("out_refund", "in_refund"):
                fiscal_type = self.env["account.fiscal.type"].search(
                    [("type", "=", inv.type)], limit=1
                )
                inv.fiscal_type_id = fiscal_type.id
            else:
                fiscal_type = inv.fiscal_type_id

            if (
                inv.is_l10n_do_fiscal_invoice
                and fiscal_type
                and fiscal_type.assigned_sequence
            ):

                inv.assigned_sequence = fiscal_type.assigned_sequence
                inv.fiscal_position_id = fiscal_type.fiscal_position_id

                domain = [
                    ("company_id", "=", inv.company_id.id),
                    ("fiscal_type_id", "=", fiscal_type.id),
                    ("state", "=", "active"),
                ]
                if inv.date_invoice:
                    domain.append(("expiration_date", ">=", inv.date_invoice))
                else:
                    today = fields.Date.context_today(inv)
                    domain.append(("expiration_date", ">=", today))

                fiscal_sequence_id = inv.env["account.fiscal.sequence"].search(
                    domain, order="expiration_date, id desc", limit=1,
                )

                if not fiscal_sequence_id:
                    pass
                elif fiscal_sequence_id.state == "active":
                    inv.fiscal_sequence_id = fiscal_sequence_id
                else:
                    inv.fiscal_sequence_id = False
            else:
                inv.fiscal_sequence_id = False

    @api.multi
    @api.depends(
        "fiscal_sequence_id",
        "fiscal_sequence_id.sequence_remaining",
        "fiscal_sequence_id.remaining_percentage",
        "state",
        "journal_id",
    )
    def _compute_fiscal_sequence_status(self):
        """ Identify the percentage fiscal sequences that has been used so far.
            With this result the user can be warned if it's above the threshold
            or if there's no more sequences available.
        """
        for inv in self:

            if not inv.is_l10n_do_fiscal_invoice or not inv.fiscal_sequence_id:
                inv.fiscal_sequence_status = "no_fiscal"
            else:
                fs_id = inv.fiscal_sequence_id  # Fiscal Sequence
                remaining = fs_id.sequence_remaining
                remaining_percent = fs_id.remaining_percentage
                seq_length = fs_id.sequence_end - fs_id.sequence_start + 1

                consumed_percent = round(1 - (remaining / seq_length), 2) * 100

                if consumed_percent < remaining_percent:
                    inv.fiscal_sequence_status = "fiscal_ok"
                elif remaining > 0 and consumed_percent >= remaining_percent:
                    inv.fiscal_sequence_status = "almost_no_sequence"
                else:
                    inv.fiscal_sequence_status = "no_sequence"

    @api.multi
    @api.constrains("state", "tax_line_ids")
    def validate_special_exempt(self):
        """ Validates an invoice with Regímenes Especiales fiscal type
            does not contain nor ITBIS or ISC.
            See DGII Norma 05-19, Art 3 for further information.
        """
        for inv in self.filtered(lambda i: i.is_l10n_do_fiscal_invoice):
            if (
                inv.type == "out_invoice"
                and inv.state in ("open", "cancel")
                and ncf_dict.get(inv.fiscal_type_id.prefix) == "especial"
            ):
                # If any invoice tax in ITBIS or ISC
                taxes = ("ITBIS", "ISC")
                if any(
                    [
                        tax
                        for tax in inv.tax_line_ids.mapped("tax_id").filtered(
                            lambda tax: tax.tax_group_id.name in taxes
                            and tax.amount != 0
                        )
                    ]
                ):
                    raise UserError(
                        _(
                            "You cannot validate and invoice of Fiscal Type "
                            "Regímen Especial with ITBIS/ISC.\n\n"
                            "See DGII General Norm 05-19, Art. 3 for further "
                            "information"
                        )
                    )

    @api.multi
    @api.constrains("state", "invoice_line_ids", "partner_id")
    def validate_products_export_ncf(self):
        """ Validates that an invoices with a partner from country != DO
            and products type != service must have Exportaciones NCF.
            See DGII Norma 05-19, Art 10 for further information.
        """
        for inv in self:
            if (
                inv.type == "out_invoice"
                and inv.state in ("open", "cancel")
                and inv.partner_id.country_id
                and inv.partner_id.country_id.code != "DO"
                and inv.is_l10n_do_fiscal_invoice
            ):
                if any(
                    [
                        p
                        for p in inv.invoice_line_ids.mapped("product_id")
                        if p.type != "service"
                    ]
                ):
                    if ncf_dict.get(inv.fiscal_type_id.prefix) == "exterior":
                        raise UserError(
                            _(
                                "Goods sales to overseas customers must have "
                                "Exportaciones Fiscal Type"
                            )
                        )
                elif ncf_dict.get(inv.fiscal_type_id.prefix) == "consumo":
                    raise UserError(
                        _(
                            "Service sales to oversas customer must have "
                            "Consumo Fiscal Type"
                        )
                    )

    @api.multi
    @api.constrains("state", "tax_line_ids")
    def validate_informal_withholding(self):
        """ Validates an invoice with Comprobante de Compras has 100% ITBIS
            withholding.
            See DGII Norma 05-19, Art 7 for further information.
        """
        for inv in self.filtered(
            lambda i: i.type == "in_invoice" and i.state == "open"
        ):
            if (
                ncf_dict.get(inv.fiscal_type_id.prefix) == "informal"
                and inv.is_l10n_do_fiscal_invoice
            ):

                # If the sum of all taxes of category ITBIS is not 0
                if sum(
                    [
                        tax.amount
                        for tax in inv.tax_line_ids.mapped("tax_id").filtered(
                            lambda t: t.tax_group_id.name == "ITBIS"
                        )
                    ]
                ):
                    raise UserError(_("You must withhold 100% of ITBIS"))

    @api.onchange("journal_id", "partner_id")
    def _onchange_journal_id(self):
        """ Set the Fiscal Type and the Fiscal Sequence to False, if the
            invoice is not a fiscal invoice for l10n_do.
        """
        if not self.is_l10n_do_fiscal_invoice:
            self.fiscal_type_id = False
            self.fiscal_sequence_id = False

        return super(AccountInvoice, self)._onchange_journal_id()

    @api.onchange("fiscal_type_id")
    def _onchange_fiscal_type(self):
        """ Set the Journal to a fiscal journal if a Fiscal Type is set to the
            invoice, making it a a fiscal invoice for l10n_do.
        """
        if self.is_l10n_do_fiscal_invoice and self.fiscal_type_id:
            if ncf_dict.get(self.fiscal_type_id.prefix) == "minor":
                self.partner_id = self.company_id.partner_id

            fiscal_type = self.fiscal_type_id
            fiscal_type_journal = fiscal_type.journal_id
            if fiscal_type_journal and fiscal_type_journal != self.journal_id:
                self.journal_id = fiscal_type_journal

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """ Set the Journal to a fiscal journal if a Fiscal Type is set to the
            invoice, making it a a fiscal invoice for l10n_do.
        """
        if self.is_l10n_do_fiscal_invoice:
            if self.partner_id and self.type == "out_invoice":
                if not self.fiscal_type_id:
                    self.fiscal_type_id = self.partner_id.sale_fiscal_type_id
                if not self.partner_id.customer:
                    self.partner_id.customer = True
            elif self.partner_id and self.type == "in_invoice":
                self.expense_type = self.partner_id.expense_type
                if not self.partner_id.supplier:
                    self.partner_id.supplier = True
                if self.partner_id.id == self.company_id.partner_id.id:
                    fiscal_type = self.env["account.fiscal.type"].search(
                        [("type", "=", self.type), ("prefix", "=", "B13")], limit=1
                    )
                    if not fiscal_type:
                        raise ValidationError(
                            _(
                                "A fiscal type for Minor Expenses does not exist"
                                " and you have to create one."
                            )
                        )
                    self.fiscal_type_id = fiscal_type
                    return super(AccountInvoice, self)._onchange_partner_id()
                self.fiscal_type_id = self.partner_id.purchase_fiscal_type_id

        return super(AccountInvoice, self)._onchange_partner_id()

    @api.onchange("reference", "origin_out")
    def _onchange_ncf(self):
        if self.is_l10n_do_fiscal_invoice:
            if ncf_dict.get(self.fiscal_type_id.prefix) in (
                "fiscal",
                "informal",
                "minor",
            ):
                self.validate_fiscal_purchase()

            if self.origin_out and (
                self.type == "out_refund" or self.type == "in_refund"
            ):
                if ncf_dict.get(self.fiscal_type_id.prefix) in (
                    "fiscal",
                    "informal",
                    "minor",
                ):
                    ncf = self.origin_out
                    if (ncf[-10:-8] != "04" or ncf[1:3] != "34") and 
                        not ncf_validation.is_valid(ncf):
                        raise UserError(
                            _(
                                "NCF wrongly typed\n\n"
                                "This NCF *{}* does not have the proper structure "
                                "please validate if you have typed it correctly."
                            ).format(ncf)
                        )

    @api.multi
    def action_invoice_open(self):
        """ Before an invoice is changed to the 'open' state, validate that all
            informations are valid regarding Norma 05-19 and if there are
            available sequences to be used just before validation
        """
        for inv in self:

            if inv.amount_untaxed == 0:
                raise UserError(
                    _(
                        u"You cannot validate an invoice whose "
                        u"total amount is equal to 0"
                    )
                )

            if inv.is_l10n_do_fiscal_invoice:

                # Because a Fiscal Sequence can be depleted while an invoice
                # is waiting to be validated, compute fiscal_sequence_id again
                # on invoice validate.
                inv._compute_fiscal_sequence()

                if not inv.fiscal_sequence_id and inv.fiscal_type_id.assigned_sequence:
                    raise ValidationError(
                        _(
                            "There is not active Fiscal Sequence for this type"
                            "of document."
                        )
                    )

                if inv.type == "out_invoice":
                    if not inv.partner_id.sale_fiscal_type_id:
                        inv.partner_id.sale_fiscal_type_id = inv.fiscal_type_id

                if inv.type == "in_invoice":

                    if not inv.partner_id.purchase_fiscal_type_id:
                        inv.partner_id.purchase_fiscal_type_id = inv.fiscal_type_id
                    if not inv.partner_id.expense_type:
                        inv.partner_id.expense_type = inv.expense_type

                if inv.fiscal_type_id.requires_document and not inv.partner_id.vat:
                    raise UserError(
                        _(
                            "Partner [{}] {} doesn't have RNC/Céd, "
                            "is required for NCF type {}"
                        ).format(
                            inv.partner_id.id,
                            inv.partner_id.name,
                            inv.fiscal_type_id.name,
                        )
                    )

                elif inv.type in ("out_invoice", "out_refund"):
                    if (
                        inv.amount_untaxed_signed >= 250000
                        and inv.fiscal_type_id.prefix != "B12"
                        and not inv.partner_id.vat
                    ):
                        raise UserError(
                            _(
                                u"if the invoice amount is greater than "
                                u"RD$250,000.00 "
                                u"the customer should have RNC or Céd"
                                u"for make invoice"
                            )
                        )

        return super(AccountInvoice, self).action_invoice_open()

    @api.multi
    def validate_fiscal_purchase(self):
        for inv in self.filtered(
            lambda i: i.type == "in_invoice" and i.state == "draft"
        ):
            ncf = inv.reference if inv.reference else None
            if ncf and ncf_dict.get(inv.fiscal_type_id.prefix) == "fiscal":
                if ncf[-10:-8] == "02" or ncf[1:3] == "32":
                    raise ValidationError(
                        _(
                            "NCF *{}* does not correspond with the fiscal type\n\n"
                            "You cannot register Consumo (02 or 32) for purchases"
                        ).format(ncf)
                    )

                elif inv.fiscal_type_id.requires_document and not inv.partner_id.vat:
                    raise ValidationError(
                        _(
                            "Partner [{}] {} doesn't have RNC/Céd, "
                            "is required for NCF type {}"
                        ).format(
                            inv.partner_id.id,
                            inv.partner_id.name,
                            inv.fiscal_type_id.name,
                        )
                    )

                elif not ncf_validation.is_valid(ncf):
                    raise UserError(
                        _(
                            "NCF wrongly typed\n\n"
                            "This NCF *{}* does not have the proper structure, "
                            "please validate if you have typed it correctly."
                        ).format(ncf)
                    )

                # TODO move this to l10n_do_external_validation_ncf
                elif not ncf_validation.check_dgii(self.partner_id.vat, ncf):
                    raise ValidationError(
                        _(
                            "NCF rejected by DGII\n\n"
                            "NCF *{}* of supplier *{}* was rejected by DGII's "
                            "validation service. Please validate if the NCF and "
                            "the supplier RNC are type correctly. Otherwhise "
                            "your supplier might not have this sequence approved "
                            "yet."
                        ).format(ncf, self.partner_id.name)
                    )

                ncf_in_invoice = (
                    inv.search_count(
                        [
                            ("id", "!=", inv.id),
                            ("company_id", "=", inv.company_id.id),
                            ("partner_id", "=", inv.partner_id.id),
                            ("reference", "=", ncf),
                            ("state", "in", ("draft", "open", "paid", "cancel")),
                            ("type", "in", ("in_invoice", "in_refund")),
                        ]
                    )
                    if inv.id
                    else inv.search_count(
                        [
                            ("partner_id", "=", inv.partner_id.id),
                            ("company_id", "=", inv.company_id.id),
                            ("reference", "=", ncf),
                            ("state", "in", ("draft", "open", "paid", "cancel")),
                            ("type", "in", ("in_invoice", "in_refund")),
                        ]
                    )
                )

                if ncf_in_invoice:
                    raise ValidationError(
                        _(
                            "NCF already used in another invoice\n\n"
                            "The NCF *{}* has already been registered in another "
                            "invoice with the same supplier. Look for it in "
                            "invoices with canceled or draft states"
                        ).format(ncf)
                    )

    @api.multi
    def invoice_validate(self):
        """ After all invoice validation routine, consume a NCF sequence and
            write it into reference field.
         """
        for inv in self:
            if (
                inv.is_l10n_do_fiscal_invoice
                and not inv.reference
                and inv.fiscal_type_id.assigned_sequence
            ):
                expiration_date = inv.fiscal_sequence_id.expiration_date
                inv.reference = inv.fiscal_sequence_id.get_fiscal_number()
                inv.ncf_expiration_date = expiration_date

        return super(AccountInvoice, self).invoice_validate()

    @api.multi
    def invoice_print(self):
        # Companies which has installed l10n_do localization use
        # l10n_do fiscal invoice template
        l10n_do_coa = self.env.ref("l10n_do.do_chart_template")
        if self.journal_id.company_id.chart_template_id.id == l10n_do_coa.id:
            report_id = self.env.ref("l10n_do_accounting.l10n_do_account_invoice")
            return report_id.report_action(self)

        return super(AccountInvoice, self).invoice_print()

    @api.model
    def _prepare_refund(
        self, invoice, date_invoice=None, date=None, description=None, journal_id=None
    ):
        """ Inherit Odoo's _prepare_refund() method to allow the use of fiscal
            types and other required fields for l10n_do.
        """
        context = dict(self._context or {})
        refund_type = context.get("refund_type")
        amount = context.get("amount")
        account = context.get("account")
        refund_reference = context.get("refund_reference")

        res = super(AccountInvoice, self)._prepare_refund(
            invoice,
            date_invoice=date_invoice,
            date=date,
            description=description,
            journal_id=journal_id,
        )

        if refund_type and refund_type != "full_refund":
            res["tax_line_ids"] = False
            res["invoice_line_ids"] = [
                (
                    0,
                    0,
                    {"name": description, "price_unit": amount, "account_id": account},
                )
            ]

        if not self.is_l10n_do_fiscal_invoice:
            return res

        fiscal_type = {"out_invoice": "out_refund", "in_invoice": "in_refund"}

        fiscal_type_id = self.env["account.fiscal.type"].search(
            [("type", "=", fiscal_type[self.type])], limit=1
        )

        if not fiscal_type_id:
            raise ValidationError(_("No Fiscal Type found for Credit Note"))

        res.update(
            {
                "reference": refund_reference,
                "origin_out": self.reference,
                "income_type": self.income_type,
                "expense_type": self.expense_type,
                "fiscal_type_id": fiscal_type_id.id,
            }
        )

        return res

    @api.multi
    @api.returns("self")
    def refund(self, date_invoice=None, date=None, description=None, journal_id=None):

        context = dict(self._context or {})
        refund_type = context.get("refund_type")
        amount = context.get("amount")
        account = context.get("account")

        if not refund_type:
            return super(AccountInvoice, self).refund(
                date_invoice=date_invoice,
                date=date,
                description=description,
                journal_id=journal_id,
            )

        new_invoices = self.browse()
        for invoice in self:
            # create the new invoice
            values = self.with_context(
                refund_type=refund_type, amount=amount, account=account
            )._prepare_refund(
                invoice,
                date_invoice=date_invoice,
                date=date,
                description=description,
                journal_id=journal_id,
            )
            refund_invoice = self.create(values)
            if invoice.type == "out_invoice":
                message = _(
                    "This customer invoice credit note has been created from: "
                    "<a href=# data-oe-model=account.invoice data-oe-id=%d>%s"
                    "</a><br>Reason: %s"
                ) % (invoice.id, invoice.number, description)
            else:
                message = _(
                    "This vendor bill credit note has been created from: <a "
                    "href=# data-oe-model=account.invoice data-oe-id=%d>%s</a>"
                    "<br>Reason: %s"
                ) % (invoice.id, invoice.number, description)

            refund_invoice.message_post(body=message)
            refund_invoice._compute_fiscal_sequence()
            new_invoices += refund_invoice
        return new_invoices

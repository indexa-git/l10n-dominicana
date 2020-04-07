import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_l10n_do_cancellation_type(self):
        """ Return the list of cancellation types required by DGII. """
        return [
            ('01', _('01 - Pre-printed Invoice Impairment')),
            ('02', _('02 - Printing Errors (Pre-printed Invoice)')),
            ('03', _('03 - Defective Printing')),
            ('04', _('04 - Correction of Product Information')),
            ('05', _('05 - Product Change')),
            ('06', _('06 - Product Return')),
            ('07', _('07 - Product Omission')),
            ('08', _('08 - NCF Sequence Errors')),
            ('09', _('09 - For Cessation of Operations')),
            ('10', _('10 - Lossing or Hurting Of Counterfoil')),
        ]

    def _get_l10n_do_income_type(self):
        """ Return the list of income types required by DGII. """
        return [
            ('01', _('01 - Operational Incomes')),
            ('02', _('02 - Financial Incomes')),
            ('03', _('03 - Extraordinary Incomes')),
            ('04', _('04 - Leasing Incomes')),
            ('05', _('05 - Income for Selling Depreciable Assets')),
            ('06', _('06 - Other Incomes')),
        ]

    def _get_l10n_do_expense_type(self):
        """ Return the list of expense types required by DGII. """
        # TODO: use self.env["res.partner"]._fields['l10n_do_expense_type'].selection
        return [
            ('01', _('01 - Personal')),
            ('02', _('02 - Work, Supplies and Services')),
            ('03', _('03 - Leasing')),
            ('04', _('04 - Fixed Assets')),
            ('05', _('05 - Representation')),
            ('06', _('06 - Admitted Deductions')),
            ('07', _('07 - Financial Expenses')),
            ('08', _('08 - Extraordinary Expenses')),
            ('09', _('09 - Cost & Expenses part of Sales')),
            ('10', _('10 - Assets Acquisitions')),
            ('11', _('11 - Insurance Expenses')),
        ]

    l10n_do_expense_type = fields.Selection(
        selection='_get_l10n_do_expense_type',
        string="Cost & Expense Type",
    )

    l10n_do_cancellation_type = fields.Selection(
        selection='_get_l10n_do_cancellation_type',
        string='Cancellation Type',
        copy=False,
    )

    l10n_do_income_type = fields.Selection(
        selection='_get_l10n_do_income_type',
        string='Income Type',
        copy=False,
        default=lambda self: self._context.get('l10n_do_income_type', '01'),
    )

    l10n_do_origin_ncf = fields.Char(string="Modifies",)

    ncf_expiration_date = fields.Date(string='Valid until', store=True,)
    is_debit_note = fields.Boolean()
    cancellation_type = fields.Selection(
        selection='_get_l10n_do_cancellation_type',
        string="Cancellation Type",
        copy=False,
    )

    def button_cancel(self):

        fiscal_invoice = self.filtered(
            lambda inv: inv.l10n_latam_country_code == 'DO' and self.type[-6:] in ('nvoice', 'refund'))

        if len(fiscal_invoice) > 1:
            raise ValidationError(
                _("You cannot cancel multiple fiscal invoices at a time."))

        if fiscal_invoice:
            action = self.env.ref(
                'l10n_do_accounting.action_account_move_cancel'
            ).read()[0]
            action['context'] = {'default_move_id': fiscal_invoice.id}
            return action

        return super(AccountMove, self).button_cancel()

    def _compute_is_debit_note(self):
        self.ensure_one()
        if (
            self.journal_id.l10n_latam_use_documents
            and self.journal_id.company_id.country_id == self.env.ref('base.do')
            and self.type == 'out_invoice'
            and self.ref
        ):
            return True if self.ref[-10:-8] == '03' else False

    @api.depends('ref')
    def _compute_l10n_latam_document_number(self):
        l10n_do_recs = self.filtered(lambda x: x.l10n_latam_country_code == 'DO')
        for rec in l10n_do_recs:
            rec.l10n_latam_document_number = rec.ref
        remaining = self - l10n_do_recs
        remaining.l10n_latam_document_number = False
        super(AccountMove, remaining)._compute_l10n_latam_document_number()

    @api.onchange('l10n_latam_document_type_id', 'l10n_latam_document_number')
    def _inverse_l10n_latam_document_number(self):
        for rec in self.filtered('l10n_latam_document_type_id'):
            if not rec.l10n_latam_document_number:
                rec.ref = ''
            else:
                if rec.l10n_latam_document_type_id.l10n_do_ncf_type:
                    l10n_latam_document_number = (rec.l10n_latam_document_type_id
                                                  ._format_document_number(
                                                      rec.l10n_latam_document_number)
                                                  )
                else:
                    l10n_latam_document_number = rec.l10n_latam_document_number

                if rec.l10n_latam_document_number != l10n_latam_document_number:
                    rec.l10n_latam_document_number = l10n_latam_document_number
                rec.ref = l10n_latam_document_number
        super(
            AccountMove, self.filtered(lambda m: m.l10n_latam_country_code != 'DO')
        )._inverse_l10n_latam_document_number()

    def _get_l10n_latam_documents_domain(self):
        self.ensure_one()
        domain = super()._get_l10n_latam_documents_domain()
        if (
            self.journal_id.l10n_latam_use_documents
            and self.journal_id.company_id.country_id == self.env.ref('base.do')
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
                domain.append(('code', 'in', codes))
        return domain

    def _get_document_type_sequence(self):
        """ Return the match sequences for the given journal and invoice """
        self.ensure_one()
        if (
            self.journal_id.l10n_latam_use_documents
            and self.l10n_latam_country_code == 'DO'
        ):
            res = self.journal_id.l10n_do_sequence_ids.filtered(
                lambda x: x.l10n_latam_document_type_id
                == self.l10n_latam_document_type_id
            )
            return res
        return super()._get_document_type_sequence()

    @api.constrains('type', 'l10n_latam_document_type_id')
    def _check_invoice_type_document_type(self):
        super()._check_invoice_type_document_type()
        for rec in self.filtered(
            lambda r: r.company_id.country_id == self.env.ref('base.do')
            and r.l10n_latam_document_type_id
        ):
            partner_vat = rec.partner_id.vat
            l10n_latam_document_type = rec.l10n_latam_document_type_id
            if not partner_vat and l10n_latam_document_type.is_vat_required:
                raise ValidationError(
                    _(
                        'A VAT is mandatory for this type of NCF. '
                        'Please set the current VAT of this client'
                    )
                )

            elif rec.type in ("out_invoice", "out_refund"):
                if (
                    rec.amount_untaxed_signed >= 250000
                    and l10n_latam_document_type.l10n_do_ncf_type != 'special'
                    and not rec.partner_id.vat
                ):
                    raise UserError(
                        _(
                            "If the invoice amount is greater than RD$250,000.00 "
                            "the customer should have a VAT to validate the invoice"
                        )
                    )

    @api.constrains('state', 'line_ids', 'l10n_latam_document_type_id')
    def _check_special_exempt(self):
        """ Validates that an invoice with a Special Tax Payer type does not contain
            nor ITBIS or ISC.
            See DGII Norma 05-19, Art 3 for further information.
        """
        for rec in self.filtered(
            lambda r: r.company_id.country_id == self.env.ref('base.do')
            and r.l10n_latam_document_type_id
            and r.type == 'out_invoice'
            and r.state in ('draft', 'cancel')
        ):
            if rec.l10n_latam_document_type_id.l10n_do_ncf_type == 'special':
                # If any invoice tax in ITBIS or ISC
                taxes = ('ITBIS', 'ISC')
                if any(
                    [
                        tax
                        for tax in rec.line_ids.filtered('tax_line_id').filtered(
                            lambda tax: tax.tax_group_id.name in taxes
                            and tax.tax_base_amount != 0
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

    @api.constrains('state')
    def _check_invoice_amount(self):
        """ Validates that an invoices has an amount greater than 0.
        """
        for rec in self.filtered(
            lambda r: r.company_id.country_id == self.env.ref('base.do')
            and r.l10n_latam_document_type_id
            and r.type == 'out_invoice'
        ):
            if rec.amount_untaxed_signed == 0:
                raise UserError(
                    _("You cannot validate an invoice with a total amount equals to 0.")
                )

    @api.constrains('state', 'line_ids', 'partner_id')
    def _check_products_export_ncf(self):
        """ Validates that an invoices with a partner from country != DO
            and products type != service must have Exportaciones NCF.
            See DGII Norma 05-19, Art 10 for further information.
        """
        for rec in self.filtered(
            lambda r: r.company_id.country_id == self.env.ref('base.do')
            and r.l10n_latam_document_type_id
            and r.type == 'out_invoice'
            and r.state in ('posted', 'cancel')
        ):
            if rec.partner_id.country_id and rec.partner_id.country_id.code != 'DO':
                if any(
                    [
                        p
                        for p in rec.invoice_line_ids.mapped('product_id')
                        if p.type != 'service'
                    ]
                ):
                    if rec.l10n_latam_document_type_id.l10n_do_ncf_type != 'export':
                        raise UserError(
                            _(
                                "Goods sales to overseas customers must have "
                                "Exportaciones Fiscal Type"
                            )
                        )
                elif rec.l10n_latam_document_type_id.l10n_do_ncf_type != 'consumer':
                    raise UserError(
                        _(
                            "Services sales to oversas customer must have "
                            "Consumo Fiscal Type"
                        )
                    )

    @api.constrains('state', 'line_ids')
    def _check_informal_withholding(self):
        """ Validates an invoice with Comprobante de Compras has 100% ITBIS
            withholding.
            See DGII Norma 05-19, Art 7 for further information.
        """
        for rec in self.filtered(
            lambda r: r.company_id.country_id == self.env.ref('base.do')
            and r.l10n_latam_document_type_id
            and r.type == 'in_invoice'
            and r.state in ('draft')
        ):

            if rec.l10n_latam_document_type_id.l10n_do_ncf_type == 'informal':
                # If the sum of all taxes of category ITBIS is not 0
                if sum(
                    [
                        tax.amount
                        for tax in rec.line_ids.tax_ids.filtered(
                            lambda tax: tax.tax_group_id.name == 'ITBIS'
                        )
                    ]
                ):
                    raise UserError(_("You must withhold 100% of ITBIS"))

    @api.onchange("l10n_latam_document_number", "l10n_do_origin_ncf")
    def _onchange_l10n_latam_document_number(self):
        for rec in self.filtered(
            lambda r: r.company_id.country_id == self.env.ref('base.do')
            and r.l10n_latam_document_type_id.l10n_do_ncf_type is not False
            and r.l10n_latam_document_number
        ):
            rec.l10n_latam_document_type_id._format_document_number(
                rec.l10n_latam_document_number
            )

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.company_id.country_id == self.env.ref('base.do') \
                and self.l10n_latam_document_type_id and self.type == 'in_invoice' \
                and self.partner_id:
            self.l10n_do_expense_type = self.partner_id.l10n_do_expense_type if not \
                self.l10n_do_expense_type else self.l10n_do_expense_type

        return super(AccountMove, self)._onchange_partner_id()

    @api.constrains('name', 'partner_id', 'company_id')
    def _check_unique_vendor_number(self):
        for rec in self.filtered(
            lambda x: x.is_purchase_document()
            and x.company_id.country_id == self.env.ref('base.do')
            and x.l10n_latam_use_documents
            and x.l10n_latam_document_number
        ):
            pass
            # domain = [
            #     ('type', '=', rec.type),
            #     ('l10n_latam_document_number', '=', rec.l10n_latam_document_number),
            #     ('company_id', '=', rec.company_id.id),
            #     ('id', '!=', rec.id),
            #     ('commercial_partner_id', '=', rec.commercial_partner_id.id),
            # ]
            # if rec.search(domain):
            #     raise ValidationError(
            #         _(
            #             "NCF already used in another invoice\n\n"
            #             "The NCF *{}* has already been registered in another "
            #             "invoice with the same supplier. Look for it in "
            #             "invoices with canceled or draft states"
            #         ).format(rec.l10n_latam_document_number)
            #     )

    @api.constrains('state', 'partner_id', 'l10n_latam_document_number')
    def _check_fiscal_purchase(self):
        for rec in self.filtered(
            lambda r: r.company_id.country_id == self.env.ref('base.do')
            and r.l10n_latam_document_type_id.l10n_do_ncf_type is not False
            and r.type == 'in_invoice'
            and r.l10n_latam_document_number
        ):
            l10n_latam_document_number = rec.l10n_latam_document_number
            l10n_latam_document_type = rec.l10n_latam_document_type_id.l10n_do_ncf_type

            if l10n_latam_document_number and l10n_latam_document_type == 'fiscal':
                if l10n_latam_document_number[-10:-8] == '02':
                    raise ValidationError(
                        _(
                            "NCF *{}* does not correspond with the fiscal type\n\n"
                            "You cannot register Consumo NCF (02) for purchases"
                        ).format(l10n_latam_document_number)
                    )

                try:
                    from stdnum.do import ncf as ncf_validation

                    if len(l10n_latam_document_number) == '11' and not ncf_validation.check_dgii(
                        rec.partner_id.vat, l10n_latam_document_number
                    ):
                        raise ValidationError(
                            _(
                                "NCF rejected by DGII\n\n"
                                "NCF *{}* of supplier *{}* was rejected by DGII's "
                                "validation service. Please validate if the NCF and "
                                "the supplier RNC are type correctly. Otherwhise "
                                "your supplier might not have this sequence approved "
                                "yet."
                            ).format(l10n_latam_document_number, rec.partner_id.name)
                        )

                except (ImportError, IOError) as err:
                    _logger.debug(err)

    def _reverse_move_vals(self, default_values, cancel=True):

        ctx = self.env.context
        amount = ctx.get('amount')
        percentage = ctx.get('percentage')
        refund_type = ctx.get('refund_type')
        reason = ctx.get('reason')

        res = super(AccountMove, self)._reverse_move_vals(
            default_values=default_values, cancel=cancel
        )

        if self.l10n_latam_country_code == 'DO':
            res['l10n_do_origin_ncf'] = self.l10n_latam_document_number

        if refund_type in ('percentage', 'fixed_amount'):
            price_unit = (
                amount
                if refund_type == "fixed_amount"
                else self.amount_untaxed * (percentage / 100)
            )
            res['line_ids'] = False
            res['invoice_line_ids'] = [(0, 0, {
                'name': reason or _("Refund"),
                'price_unit': price_unit,
            })]
        return res

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
        return [
            ('01', _('01 - Personal')),
            ('02', _('02 - Work, Supplies and Services')),
            ('03', _('03 - Leases')),
            ('04', _('04 - Fix Assets')),
            ('05', _('05 - Representation')),
            ('06', _('06 - Other Allowed Deductions')),
            ('07', _('07 - Financial Expenses')),
            ('08', _('08 - Extraordinary Expenses')),
            ('09', _('09 - Part of the COGS')),
            ('10', _('10 - Assets adquisition')),
            ('11', _('11 - Insurance Expeses')),
        ]

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

    l10n_do_expense_type = fields.Selection(
        selection='_get_l10n_do_expense_type', string='Expense Type',
    )

    l10n_do_origin_ncf = fields.Char(string="Modifies",)

    ncf_expiration_date = fields.Date(string='Valid until', store=True,)

    l10n_latam_document_number = fields.Char(store=True)

    def _compute_is_debit_note(self):
        self.ensure_one()
        if (
            self.journal_id.l10n_latam_use_documents
            and self.journal_id.company_id.country_id == self.env.ref('base.do')
            and self.type == 'out_invoice'
            and self.ref
        ):
            return True if self.ref[-10:-8] == '03' else False

    @api.depends('name')
    def _compute_l10n_latam_document_number(self):
        recs_with_name = self.filtered(lambda x: x.name != '/')
        for rec in recs_with_name:
            name = rec.name
            doc_code_prefix = rec.l10n_latam_document_type_id.doc_code_prefix
            if doc_code_prefix and name:
                name = name.split(" ", 1)[-1]
            rec.l10n_latam_document_number = rec.l10n_latam_document_number
        remaining = self - recs_with_name
        remaining.l10n_latam_document_number = False

    @api.onchange('l10n_latam_document_type_id', 'l10n_latam_document_number')
    def _inverse_l10n_latam_document_number(self):
        moves = self.filtered(lambda m: m.l10n_latam_country_code != 'DO')

        for rec in moves.filtered('l10n_latam_document_type_id'):
            if not rec.l10n_latam_document_number:
                rec.name = '/'
            else:
                l10n_latam_document_number = (rec.l10n_latam_document_type_id
                                              ._format_document_number(
                                                  rec.l10n_latam_document_number)
                                              )
                if rec.l10n_latam_document_number != l10n_latam_document_number:
                    rec.l10n_latam_document_number = l10n_latam_document_number

        super(AccountMove, moves)._inverse_l10n_latam_document_number()

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
                ('l10n_do_ncf_type', 'in', ncf_types),
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
            tax_payer_type = rec.partner_id.l10n_do_dgii_tax_payer_type
            latam_document_type_code = rec.l10n_latam_document_type_id.l10n_do_ncf_type
            if not tax_payer_type and latam_document_type_code not in [
                '01',
                '03',
                '04',
                '14',
                '15',
            ]:
                raise ValidationError(
                    _(
                        'Tax payer type is mandatory for this type of document. '
                        'Please set the current tax payer type of this client'
                    )
                )

    # TODO: This constraint is executing when it wants
    @api.constrains('state', 'line_ids.tax_line_id', 'l10n_latam_document_type_id')
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
            if rec.partner_id.l10n_do_dgii_tax_payer_type == 'special':
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
            and r.state in ('draft', 'cancel')
        ):
            if rec.partner_id.country_id and rec.partner_id.country_id.code != 'DO':
                if any(
                    [
                        p
                        for p in rec.invoice_line_ids.mapped('product_id')
                        if p.type != 'service'
                    ]
                ):
                    if rec.partner_id.l10n_do_dgii_tax_payer_type != 'exterior':
                        raise UserError(
                            _(
                                "Goods sales to overseas customers must have "
                                "Exportaciones Fiscal Type"
                            )
                        )
                elif rec.partner_id.l10n_do_dgii_tax_payer_type != 'consumo':
                    raise UserError(
                        _(
                            "Services sales to oversas customer must have "
                            "Consumo Fiscal Type"
                        )
                    )

    @api.constrains('state', 'line_ids.tax_line_id')
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

            if rec.partner_id.l10n_do_dgii_tax_payer_type == 'non_payer':
                # If the sum of all taxes of category ITBIS is not 0
                if sum(
                    [
                        tax.amount
                        for tax in rec.tax_line_ids.mapped('tax_id').filtered(
                            lambda t: t.tax_group_id.name == 'ITBIS'
                        )
                    ]
                ):
                    raise UserError(_("You must withhold 100% of ITBIS"))

    @api.onchange("l10n_latam_document_number", "l10n_do_origin_ncf")
    def _onchange_l10n_latam_document_number(self):
        for rec in self.filtered(
            lambda r: r.company_id.country_id == self.env.ref('base.do')
            and r.l10n_latam_document_type_id
            and r.state in ('draft')
            and r.l10n_latam_document_number
        ):
            rec.l10n_latam_document_type_id._format_document_number(
                rec.l10n_latam_document_number
            )

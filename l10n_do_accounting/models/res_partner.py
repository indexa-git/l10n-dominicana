from odoo import models, fields, api, _


class Partner(models.Model):
    _inherit = 'res.partner'

    def _get_l10n_do_dgii_payer_types_selection(self):
        """ Return the list of payer types needed in invoices to clasify accordingly to
        DGII requirements. """
        return [
            ('taxpayer', _('Fiscal Tax Payer')),
            ('non_payer', _('Non Tax Payer')),
            ('nonprofit', _('Nonprofit Organization')),
            ('special', _('special from Tax Paying')),
            ('governmental', _('Governmental')),
            ('foreigner', _('Foreigner')),
        ]

    l10n_do_dgii_tax_payer_type = fields.Selection(
        selection='_get_l10n_do_dgii_payer_types_selection',
        compute='_compute_l10n_do_dgii_payer_type',
        inverse='_inverse_l10n_do_dgii_tax_payer_type',
        string='Taxpayer Type',
        index=True,
        store=True,
    )

    def _get_l10n_do_expense_type(self):
        """ Return the list of expenses needed in invoices to clasify accordingly to
        DGII requirements. """
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
        string='Cost & Expense Type',
        store=True,
    )

    @api.depends('l10n_do_dgii_tax_payer_type')
    def _compute_is_fiscal_info_required(self):
        for partner in self:
            if partner.l10n_do_dgii_tax_payer_type != 'non_payer':
                partner.is_fiscal_info_required = True
            else:
                partner.is_fiscal_info_required = False

    is_fiscal_info_required = fields.Boolean(compute='_compute_is_fiscal_info_required')

    country_id = fields.Many2one(
        default=lambda self: self.env.ref('base.do')
        if self.env.user.company_id.country_id == self.env.ref('base.do')
        else False
    )

    @api.depends('vat', 'country_id', 'name')
    def _compute_l10n_do_dgii_payer_type(self):
        """ Compute the type of partner depending on soft decisions"""
        company_id = self.env['res.company'].search(
            [('id', '=', self.env.user.company_id.id)]
        )
        for partner in self:
            vat = str(partner.vat) if partner.vat else False
            is_dominican_partner = bool(partner.country_id == self.env.ref('base.do'))

            if partner.country_id and not is_dominican_partner:
                partner.l10n_do_dgii_tax_payer_type = 'foreigner'

            elif vat and (
                not partner.l10n_do_dgii_tax_payer_type
                or partner.l10n_do_dgii_tax_payer_type == 'non_payer'
            ):
                if partner.country_id and is_dominican_partner:
                    if vat.isdigit() and len(vat) == 9:
                        if partner.name and 'MINISTERIO' in partner.name:
                            partner.l10n_do_dgii_tax_payer_type = 'governmental'
                        elif partner.name and any(
                            [n for n in ('IGLESIA', 'ZONA FRANCA') if n in partner.name]
                        ):
                            partner.l10n_do_dgii_tax_payer_type = 'special'
                        elif vat.startswith('1'):
                            partner.l10n_do_dgii_tax_payer_type = 'taxpayer'
                        elif vat.startswith('4'):
                            partner.l10n_do_dgii_tax_payer_type = 'nonprofit'
                        else:
                            partner.l10n_do_dgii_tax_payer_type = 'taxpayer'

                    elif len(vat) == 11:
                        if vat.isdigit():
                            payer_type = (
                                'taxpayer'
                                if company_id.l10n_do_default_client == 'fiscal'
                                else 'non_payer'
                            )
                            partner.l10n_do_dgii_tax_payer_type = payer_type
                        else:
                            partner.l10n_do_dgii_tax_payer_type = 'non_payer'
            elif not partner.l10n_do_dgii_tax_payer_type:
                partner.l10n_do_dgii_tax_payer_type = 'non_payer'
            else:
                partner.l10n_do_dgii_tax_payer_type = (
                    partner.l10n_do_dgii_tax_payer_type
                )

    def _inverse_l10n_do_dgii_tax_payer_type(self):
        for partner in self:
            partner.l10n_do_dgii_tax_payer_type = partner.l10n_do_dgii_tax_payer_type

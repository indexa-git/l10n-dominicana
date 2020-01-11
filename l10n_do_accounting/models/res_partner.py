from odoo import models, fields, api, _


class Partner(models.Model):
    _inherit = 'res.partner'

    def _get_l10n_do_dgii_payer_types_selection(self):
        """ Returns the list of different type of customer / suppliers depending on
        their fiscal status. This is required to define the correct fiscal sequence to
        be used on invoices."""
        return [
            ('01', _('01 - Personnel Expenses')),
            ('02', _('02 - Expenses for Work, Supplies and Services')),
            ('03', _('03 - Leases')),
            ('04', _('04 - Fixed Asset Expenses')),
            ('05', _('05 - Representation Expenses')),
            ('06', _('06 - Other Deductions Admitted')),
            ('07', _('07 - Financial Expenses')),
            ('08', _('08 - Extraordinary Expenses')),
            ('09', _('09 - Purchasess and Expenses part of the Cost of Sale')),
            ('10', _('10 - Acquisitions of Assets')),
            ('11', _('11 - Insurance Expenses')),
        ]

    def _get_l10n_do_expense_type(self):
        """ Return the list of expenses needed in invoices to clasify accordingly to
        DGII requirements. """
        return [
            ('taxpayer', _('Fiscal Tax Payer')),
            ('non_payer', _('Non Tax Payer')),
            ('exempt', _('Exempt from Tax Paying')),
            ('governmental', _('Governmental')),
            ('foreigner', _('Foreigner')),
        ]

    country_id = fields.Many2one(
        default=lambda self: self.env.ref('base.do')
        if self.env.user.company_id.country_id == self.env.ref('base.do')
        else False
    )
    l10n_do_dgii_tax_payer_type = fields.Selection(
        selection='_get_l10n_do_dgii_payer_types_selection',
        compute='_compute_l10n_do_dgii_payer_type',
        inverse='_inverse_l10n_do_dgii_tax_payer_type',
        string='Taxpayer Type',
        index=True,
    )
    l10n_do_expense_type = fields.Selection(
        selection='_get_l10n_do_expense_type', string="Expense Type",
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

            if vat and not partner.l10n_do_dgii_tax_payer_type:
                if partner.country_id and is_dominican_partner:
                    if vat.isdigit() and len(vat) == 9:
                        if 'MINISTERIO' in partner.name:
                            partner.l10n_do_dgii_tax_payer_type = 'governmental'
                        elif any(
                            [n for n in ('IGLESIA', 'ZONA FRANCA') if n in partner.name]
                        ):
                            partner.l10n_do_dgii_tax_payer_type = 'exempt'
                        else:
                            partner.l10n_do_dgii_tax_payer_type = 'taxpayer'
                    elif len(vat) == 11:
                        if vat.isdigit():
                            payer_type = (
                                'fiscal'
                                if company_id.l10n_do_default_consumer == 'taxpayer'
                                else 'non_payer'
                            )
                            partner.l10n_do_dgii_tax_payer_type = payer_type
                        else:
                            partner.l10n_do_dgii_tax_payer_type = 'non_payer'
                elif partner.country_id and not is_dominican_partner:
                    partner.l10n_do_dgii_tax_payer_type = 'foreigner'
            elif not partner.l10n_do_dgii_tax_payer_type:
                partner.l10n_do_dgii_tax_payer_type = 'non_payer'
            else:
                partner.l10n_do_dgii_tax_payer_type = 'non_payer'

    def _inverse_l10n_do_dgii_tax_payer_type(self):
        for partner in self:
            partner.l10n_do_dgii_tax_payer_type = partner.l10n_do_dgii_tax_payer_type

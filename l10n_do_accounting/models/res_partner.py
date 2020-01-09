from odoo import models, fields, _


class Partner(models.Model):
    _inherit = 'res.partner'

    l10n_do_dgii_tax_payer_type = fields.Selection(
        selection='_get_l10n_do_dgii_payer_types_selection',
        string='Taxpayer Type',
        index=True,
        # TODO: add help
    )

    def _get_l10n_do_dgii_payer_types_selection(self):
        """ Return the list of values of the selection field. """
        return [
            ('taxpayer', _('Fiscal Tax Payer')),
            ('non_payer', _('Non Tax Payer')),
            ('exempt', _('Exempt from Tax Paying')),
            ('governmental', _('Governmental')),
            ('foreigner', _('Foreigner')),
        ]

    def _compute_l10n_do_dgii_payer_type(self):
        """ Compute the type of partner depending on soft decisions"""
        self.ensure_one()

        company_id = self.env['res.company'].search(
            [('id', '=', self.env.user.company_id.id)]
        )
        vat = str(self.vat)
        is_dominican_partner = bool(self.country_id == self.env.ref('base.do'))

        if vat:
            if self.country_id and is_dominican_partner:
                if vat.isdigit() and len(vat) == 9:
                    if vat.startswith('43'):
                        return 'governmental'
                    elif vat.startswith('10'):
                        return 'special'
                    elif vat.startswith('13'):
                        return 'fiscal'
                elif len(vat) == 11:
                    if vat.isdigit():
                        return (
                            'fiscal'
                            if company_id.l10n_do_default_consumer == 'fiscal'
                            else 'final'
                        )
                    else:
                        return 'final'
            elif self.country_id and not is_dominican_partner:
                return 'foreigner'
        else:
            return 'final'

    l10n_do_expense_type = fields.Selection(
        [
            ('01', '01 - Gastos de Personal'),
            ('02', '02 - Gastos por Trabajo, Suministros y Servicios'),
            ('03', '03 - Arrendamientos'),
            ('04', '04 - Gastos de Activos Fijos'),
            ('05', '05 - Gastos de Representación'),
            ('06', '06 - Otras Deducciones Admitidas'),
            ('07', '07 - Gastos Financieros'),
            ('08', '08 - Gastos Extraordinarios'),
            ('09', '09 - Compras y Gastos que forman parte del Costo de Venta'),
            ('10', '10 - Adquisiciones de Activos'),
            ('11', '11 - Gastos de Seguro'),
        ],
        string="Expense Type",
    )

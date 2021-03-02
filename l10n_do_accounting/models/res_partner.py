import json
import re

from odoo import models, fields, api, _
from odoo.exceptions import UserError

try:
    from stdnum.do import rnc, cedula
except (ImportError, IOError) as err:
    _logger.debug(str(err))
class Partner(models.Model):
    _inherit = "res.partner"

    @api.multi
    @api.depends('sale_fiscal_type_id')
    def _compute_is_fiscal_info_required(self):
        for rec in self:
            if rec.sale_fiscal_type_id.prefix in ['B01', 'B14', 'B15']:
                rec.is_fiscal_info_required = True
            else:
                rec.is_fiscal_info_required = False


    sale_fiscal_type_id = fields.Many2one(
        "account.fiscal.type",
        string="Sale Fiscal Type",
        domain=[("type", "=", "out_invoice")],
        compute='_compute_sale_fiscal_type_id',
        inverse='_inverse_sale_fiscal_type_id',
        index=True,
        store=True,
    )

    sale_fiscal_type_list = [{
        "id": "final",
        "name": "Consumo",
        "ticket_label": "Consumo",
        "is_default": True
    }, {
        "id": "fiscal",
        "name": "Crédito Fiscal"
    }, {
        "id": "gov",
        "name": "Gubernamental"
    }, {
        "id": "special",
        "name": "Regímenes Especiales"
    }, {
        "id": "unico",
        "name": "Único Ingreso"
    }, {
        "id": "export",
        "name": "Exportaciones"
    }]

    sale_fiscal_type_vat = {
        "rnc": ["fiscal", "gov", "special"],
        "ced": ["final", "fiscal"],
        "other": ["final"],
        "no_vat": ["final", "unico", "export"]
    }

    purchase_fiscal_type_id = fields.Many2one(
        "account.fiscal.type",
        string="Purchase Fiscal Type",
        domain=[("type", "=", "in_invoice")],
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
            ("11", "11 - Gastos de Seguro"),
        ],
        string="Expense Type",
    )

    is_fiscal_info_required = fields.Boolean(compute="_compute_is_fiscal_info_required")

    country_id = fields.Many2one('res.country',
                                 string='Country',
                                 ondelete='restrict',
                                 default=lambda self: self.env.ref('base.do'))

    
    def _get_fiscal_type_domain(self, prefix):
        fiscal_type = self.env[
            'account.fiscal.type'].search([
                ('type', '=', 'out_invoice'),
                ('prefix', '=', prefix),
            ], limit=1)
        
        return fiscal_type

    
    @api.depends('vat', 'country_id', 'name')
    def _compute_sale_fiscal_type_id(self):
        """ Compute the type of partner depending on soft decisions"""

        for partner in self:
            vat = str(partner.vat) if partner.vat else False
            is_dominican_partner = bool(partner.country_id == self.env.ref('base.do'))

            if partner.country_id and not is_dominican_partner:
                partner.sale_fiscal_type_id = self._get_fiscal_type_domain('B16')

            elif vat and (
                not partner.sale_fiscal_type_id
                or partner.sale_fiscal_type_id == 'final'
            ):
                if partner.country_id and is_dominican_partner:
                    if vat.isdigit() and len(vat) == 9:
                        if partner.name and 'MINISTERIO' in partner.name:
                            partner.sale_fiscal_type_id = self._get_fiscal_type_domain('B15')
                        elif partner.name and any(
                            [n for n in ('IGLESIA', 'ZONA FRANCA') if n in partner.name]
                        ):
                            partner.sale_fiscal_type_id = self._get_fiscal_type_domain('B14')
                        else:
                            partner.sale_fiscal_type_id = self._get_fiscal_type_domain('B01')

                    elif len(vat) == 11:
                        if vat.isdigit():
                            partner.sale_fiscal_type_id = self._get_fiscal_type_domain('B01')
                        else:
                            partner.sale_fiscal_type_id = self._get_fiscal_type_domain('B02')
            elif not partner.sale_fiscal_type_id:
                partner.sale_fiscal_type_id = self._get_fiscal_type_domain('B02')
            else:
                partner.sale_fiscal_type_id = (
                    partner.sale_fiscal_type_id
                )

    def _inverse_sale_fiscal_type_id(self):
        pass

    @api.onchange("vat")
    def _check_rnc(self):
        for partner_rnc in self:
            if partner_rnc.vat:
                if (
                    len(partner_rnc.vat) not in [9, 11]
                ):
                    raise UserError(
                        _(
                            "Check Vat Format or should not have any Caracter like '-'"
                        )
                    )
                    
                if (
                    not (
                        (len(partner_rnc.vat) == 9 and rnc.is_valid(partner_rnc.vat))
                        or (len(partner_rnc.vat) == 11 and cedula.is_valid(partner_rnc.vat))
                    )
                ):

                    raise UserError(
                        _(
                            "Check Vat, Seems like it's not correct"
                        )
                    )
                else:

                    result = rnc.check_dgii(partner_rnc.vat)
                    if result is not None:
                        # remove all duplicate white space from the name
                        result["name"] = " ".join(
                            re.split(r"\s+", result["name"], flags=re.UNICODE))
                        
                        partner_rnc.name = result["name"]

    @api.model
    def get_sale_fiscal_type_id_selection(self):
        return {
            "sale_fiscal_type_id": self.sale_fiscal_type_id.id,
            "sale_fiscal_type_list": self.sale_fiscal_type_list,
            "sale_fiscal_type_vat": self.sale_fiscal_type_vat
        }
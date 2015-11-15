# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
import requests
from tools import is_ncf, _internet_on


class AccountInvoice(models.Model):
    _inherit = "account.invoice"


    anulation_type = fields.Selection([
        ("01", "DETERIORO DE FACTURA PRE-IMPRESA"),
        ("02", "ERRORES DE IMPRESIÓN (FACTURA PRE-IMPRESA)"),
        ("03", u"IMPRESIÓN DEFECTUOSA"),
        ("04", "DUPLICIDAD DE FACTURA"),
        ("05", "CORRECCIÓN DE LA INFORMACIÓN"),
        ("06", "CAMBIO DE PRODUCTOS"),
        ("07", "DEVOLUCIÓN DE PRODUCTOS"),
        ("08", "OMISIÓN DE PRODUCTOS"),
        ("09", "ERRORES EN SECUENCIA DE NCF")
    ], string=u"Tipo de anulación", copy=False)
    shop_id = fields.Many2one("shop.ncf.config", string="Sucursal", required=False,
                              domain=lambda s: s.env["shop.ncf.config"].get_user_shop_domain(),
                              # default=lambda s: s.env["shop.ncf.config"].get_default_shop()
                              )
    ncf = fields.Char("NCF", size=19, copy=False)
    ncf_required = fields.Boolean()


    _sql_constraints = [
        ('number_uniq', 'unique(number, company_id, journal_id, type, partner_id)', 'Invoice Number must be unique per Company!'),
    ]


    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if self.type in ('in_invoice', 'in_refund'):
            self.ncf = False
            if self.journal_id.purchase_type == "normal":
                self.ncf_required = True
            else:
                self.ncf_required = False

        return super(AccountInvoice, self)._onchange_journal_id()

    @api.onchange("fiscal_position_id")
    def onchange_fiscal_position_id(self):

        if self.type in ('out_invoice', 'out_refund'):
            if self.fiscal_position_id.client_fiscal_type == "final":
                self.journal_id = self.shop_id.final.id
            elif self.fiscal_position_id.client_fiscal_type == "fiscal":
                self.journal_id = self.shop_id.fiscal.id
            elif self.fiscal_position_id.client_fiscal_type == "gov":
                self.journal_id = self.shop_id.gov.id
            elif self.fiscal_position_id.client_fiscal_type == "special":
                self.journal_id = self.shop_id.special.id
            else:
                self.journal_id = self.shop_id.final.id

            self.shop_id = self.env["shop.ncf.config"].get_default_shop()

        elif self.type in ('in_invoice', 'in_refund'):
            if self.partner_id.journal_id:
                self.journal_id = self.partner_id.journal_id.id
            else:
                self.journal_id = self.fiscal_position_id.journal_id.id

            if self.fiscal_position_id.supplier_fiscal_type in ("01","02","03","04","05","06","07","08","09","10","11"):
                self.ncf_required = True
            else:
                self.ncf_required = False

    def _check_ncf(self, rnc, ncf):
        if ncf and rnc:
            res = requests.get('http://api.marcos.do/ncf/{}/{}'.format(rnc, ncf))
            if res.status_code == 200:
                return res.json()
        return {}

    @api.multi
    def invoice_ncf_validation(self):
        for invoice in self:
            if not invoice.journal_id.purchase_type in ['minor', 'informal', 'exterior'] and invoice.ncf_required == True:

                inv_exist = self.search([('partner_id','=',invoice.partner_id.id),('number','=',invoice.ncf),('state','in',('open','paid'))])
                if inv_exist:
                    raise exceptions.Warning(u"Este número de comprobante ya fue registrado para este proveedor!")

                if not is_ncf(invoice.ncf, invoice.type):
                    raise exceptions.UserError("El numero de comprobante fiscal no es valido"
                                          "verifique de que no esta digitando un comprobante"
                                          "de consumidor final codigo 02 o revise si lo ha "
                                          "digitado incorrectamente")

                elif _internet_on():
                    result = self._check_ncf(invoice.partner_id.vat, invoice.ncf)
                    if not result.get("valid", False):
                        raise exceptions.UserError("El numero de comprobante fiscal no es valido! "
                                              "no paso la validacion en DGII, Verifique que el NCF y el RNC del "
                                                   "proveedor esten correctamente digitados.")

            self.signal_workflow("invoice_open")

    @api.model
    def create(self, vals):
        if self._context.get("type", False) in ('in_invoice', 'in_refund') and vals.get("ncf", False):
            vals.update({"move_name": vals["ncf"]})
        return super(AccountInvoice, self).create(vals)


    @api.multi
    def write(self, vals):
        if vals.get("ncf", False) and self._context.get("type", False) in ('in_invoice', 'in_refund'):
            vals.update({"move_name": vals["ncf"]})
        return super(AccountInvoice, self).write(vals)

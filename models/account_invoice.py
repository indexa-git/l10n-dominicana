# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
import requests
from tools import is_ncf, _internet_on


class InheritedAccountInvoice(models.Model):
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
                              # domain=lambda s: s.env["shop.ncf.config"].get_user_shop_domain(),
                              # default=lambda s: s.env["shop.ncf.config"].get_default_shop()
                              )
    ncf = fields.Char("NCF", size=19, copy=False)
    ncf_required = fields.Boolean()
    client_fiscal_type = fields.Selection(related="fiscal_position_id.client_fiscal_type")
    supplier_fiscal_type = fields.Selection(related="fiscal_position_id.supplier_fiscal_type")

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

        if self.journal_id.purchase_type == "minor":
            self.partner_id = self.env['res.company']._company_default_get('account.invoice').partner_id.id
            self.ncf_required = False


        return super(InheritedAccountInvoice, self)._onchange_journal_id()

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        super(InheritedAccountInvoice, self)._onchange_partner_id()
        if self.type in ("in_invoice","in_refund"):
            self.fiscal_position_id = self.partner_id.property_account_position_supplier_id.id

    @api.onchange("fiscal_position_id")
    def onchange_fiscal_position_id(self):

        if self.type in ('out_invoice', 'out_refund'):
            self.shop_id = self.env["shop.ncf.config"].get_default_shop()
            self.journal_id = self.shop_id.sale_journal_id.id
            if self.partner_id and self.partner_id.property_account_position_id.id != self.fiscal_position_id.id:
                self.partner_id.write({"property_account_position_id": self.fiscal_position_id.id})

        elif self.type in ('in_invoice', 'in_refund'):
            if self.partner_id.journal_id:
                self.journal_id = self.partner_id.journal_id.id
            else:
                self.journal_id = self.fiscal_position_id.journal_id.id

            if self.fiscal_position_id.supplier_fiscal_type in ("01","02","03","04","05","06","07","08","09","10","11"):
                self.ncf_required = True
            else:
                self.ncf_required = False

            if self.partner_id and self.partner_id.property_account_position_supplier_id.id != self.fiscal_position_id.id:
                self.partner_id.write({"property_account_position_supplier_id": self.fiscal_position_id.id})

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

                elif _internet_on() and self.journal_id.ncf_remote_validation:
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
        return super(InheritedAccountInvoice, self).create(vals)


    @api.multi
    def write(self, vals):
        if vals.get("ncf", False) and self._context.get("type", False) in ('in_invoice', 'in_refund'):
            vals.update({"move_name": vals["ncf"]})
        return super(InheritedAccountInvoice, self).write(vals)


class InheritedAccountInvoiceRefund(models.TransientModel):
    _inherit = 'account.invoice.refund'

    refund_ncf = fields.Char(u"NCF nota de crédito", size=19)
    invoice_type = fields.Char(default=lambda s: s._context.get("type", False))

    @api.multi
    def invoice_refund(self):
        res = super(InheritedAccountInvoiceRefund, self).invoice_refund()
        if self._context.get("type", False) == "in_invoice":
            inv = self.env['account.invoice'].browse(self._context.get("active_id"))
            refund_inv = self.env['account.invoice'].search([('origin','=',inv.number),('type','=',"in_refund")])
            refund_inv.write({"ncf": self.refund_ncf, "ncf_required": True})

        return res

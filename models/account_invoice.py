# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
import requests
from tools import is_ncf, _internet_on
import openerp.addons.decimal_precision as dp

from datetime import date, datetime

MAGIC_COLUMNS = ('id', 'create_uid', 'create_date', 'write_uid', 'write_date')


class InheritedAccountInvoice(models.Model):
    _inherit = "account.invoice"

    def _default_user_shop(self):
        shop_user_config = self.env["shop.ncf.config"].get_user_shop_config()
        return shop_user_config["shop_ids"][0]

    def _default_user_journal(self):
        shop_user_config = self.env["shop.ncf.config"].get_user_shop_config()
        return shop_user_config["sale_journal_ids"][0]

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
                              default=_default_user_shop)
    ncf = fields.Char("NCF", size=19, copy=False)
    ncf_required = fields.Boolean()
    client_fiscal_type = fields.Selection(related="fiscal_position_id.client_fiscal_type")
    supplier_fiscal_type = fields.Selection(related="fiscal_position_id.supplier_fiscal_type")
    journal_id = fields.Many2one('account.journal', string='Journal',
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=_default_user_journal,
        domain="[('type', 'in', {'out_invoice': ['sale'], 'out_refund': ['sale'], 'in_refund': ['purchase'], 'in_invoice': ['purchase']}.get(type, [])), ('company_id', '=', company_id)]")

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

    @api.onchange("payment_term_id")
    def onchange_payment_term_id(self):
        if self.payment_term_id and self.partner_id.property_payment_term_id.id != self.payment_term_id.id:
            self.env["res.partner"].browse(self.partner_id.id).write({"property_payment_term_id": self.payment_term_id.id})

    @api.onchange("fiscal_position_id")
    def onchange_fiscal_position_id(self):

        if self.type in ('out_invoice', 'out_refund'):
            if self.partner_id and self.partner_id.property_account_position_id.id != self.fiscal_position_id.id:
                self.partner_id.write({"property_account_position_id": self.fiscal_position_id.id})

            shop_user_config = self.env["shop.ncf.config"].get_user_shop_config()

            return {"domain": {
                "shop_id": [('shop_id', 'in', shop_user_config["shop_ids"])],
                "journal_id": [('id', 'in', shop_user_config["sale_journal_ids"])]
            }}

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
                    raise exceptions.UserError("El numero de comprobante fiscal no es valido "
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

    @api.model
    def _refund_cleanup_lines(self, lines):
        """ Convert records to dict of values suitable for one2many line creation

            :param recordset lines: records to convert
            :return: list of command tuple for one2many line creation [(0, 0, dict of valueis), ...]
        """

        if not lines:
            return []

        refund_type = self._context.get("refund_type", False)

        days = 0
        if lines:
            days = self.get_days_between(lines[0].invoice_id.date_invoice)

        result = []
        for line in lines:
            values = {}
            for name, field in line._fields.iteritems():
                if name in MAGIC_COLUMNS:
                    continue
                elif field.type == 'many2one':
                    values[name] = line[name].id
                elif field.type not in ['many2many', 'one2many']:
                    if name == "quantity":
                        if not refund_type:
                            values[name] = line.qty_allow_refund
                        else:
                            values["quantity"] = line[name]
                    elif name == "qty_allow_refund":
                        if not refund_type:
                            values[name] = line.qty_allow_refund
                        else:
                            values["qty_allow_refund"] = line["quantity"]
                    else:
                        values[name] = line[name]
                elif name == 'invoice_line_tax_ids':
                    if days > 30:
                        continue
                    values[name] = [(6, 0, line[name].ids)]

                values["refund_line_ref"] = line.id

            if not values:
                return []
            if lines._model == "account.invoice.line":
                if values.get("quantity", False) == 0.00:
                    continue
            result.append((0, 0, values))

        if not result:
            raise exceptions.UserError("Todos los productos de esta factura ya fueron devueltos.")

        return result

    @api.multi
    def invoice_validate(self):
        res = super(InheritedAccountInvoice, self).invoice_validate()

        if self.type in ["out_invoice", "in_invoice"]:
            for line in self.invoice_line_ids:
                line.qty_allow_refund = line.quantity
        elif self.type in ["out_refund", "in_refund"]:
            for line in self.invoice_line_ids:
                if line.quantity > line.qty_allow_refund:
                    raise exceptions.UserError("No puede devolver mas productos de que los facturados.")
                origin = self.env["account.invoice.line"].browse(line.refund_line_ref.id)
                origin.write({"qty_allow_refund": origin.qty_allow_refund-line.quantity})

            refund_inv = self.env['account.invoice'].search([('origin','=',self.number),('state','in',('open', 'paid'))])
            total_refund = sum([rec.amount_untaxed for rec in refund_inv])+self.amount_untaxed
            afected_inv = self.env['account.invoice'].search([('number','=',self.origin),('state','in',('open', 'paid'))])
            if total_refund>afected_inv.amount_untaxed:
                raise exceptions.UserError("No puede crear notas de credito por un valor mayor a la factura afectada.")
        return res

    def get_days_between(self, joining_date):

        date_format = '%Y-%m-%d'
        current_date = datetime.strptime(datetime.today().strftime(date_format), date_format)
        doc_date = datetime.strptime(joining_date, date_format)
        delta = current_date - doc_date
        return delta.days


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    qty_allow_refund = fields.Float(string='qty allow refund', digits=dp.get_precision('Product Unit of Measure'), required=False,copy=False)
    refund_line_ref = fields.Many2one("account.invoice.line", string="origin line refund", copy=False)


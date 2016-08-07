# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions


class InvoiceCurrecyChangeWizard(models.TransientModel):
    _name = "invoice.currency.change.wizard"

    def _get_currency_domain(self):
        if self.env.context.get("currency_id", False):
            return [('id','!=',self.env.context["currency_id"])]

        return[]

    currency_id = fields.Many2one("res.currency", domain=_get_currency_domain, require=True, string="Moneda")

    def _get_rate(self, rate_date):
        if self.currency_id:

            self._cr.execute("""SELECT rate FROM res_currency_rate
                               WHERE currency_id = %s
                                 AND name = %s
                                 AND (company_id is null
                                     OR company_id = %s)
                            ORDER BY company_id, name desc LIMIT 1""",
                           (self.currency_id.id, rate_date, self.env.user.company_id.id))
            if self._cr.rowcount > 0:
                return (1 / self._cr.fetchone()[0])

            return False


    @api.multi
    def update_invoice_currency(self):

        active_id = self._context.get("active_id")
        model = self._context.get("active_model")
        inv = self.env[model].browse(active_id)

        update_curr = False
        if self.currency_id.id == self.env.user.company_id.currency_id.id:
            if not inv.currency_id._get_rate(inv.date_invoice):
                update_curr = True
                default_currency_id = inv.currency_id.id

        if self.currency_id.id != self.env.user.company_id.currency_id.id:
            if not inv.currency_id._get_rate(self.date_invoice):
                update_curr = True
                default_currency_id = self.currency_id.id

        if update_curr:
            view_id = self.env.ref("currency_rates_control.update_rate_wizard_form", True)
            return {
                'name': 'Fecha sin tasa, Actualizar tasa de la moneda',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'update.rate.wizard',
                'view_id': view_id.id,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
                'context': {"default_currency_id": default_currency_id,
                            "default_name": inv.date_invoice or fields.Date.today()}
            }


        if self.currency_id.id != inv.currency_id.id:
            if self.currency_id.id == self.env.user.company_id.currency_id.id:
                for line in inv.invoice_line_ids:
                    line.price_unit = line.price_unit*inv.rate
            else:
                new_rate = self._get_rate(inv.date_invoice)
                if not new_rate:
                    raise exceptions.ValidationError(u"Antes de cambiar la mondeda de la factura debe actulizar la tasa.")
                for line in inv.invoice_line_ids:
                   line.price_unit = line.price_unit/new_rate

            inv.currency_id = self.currency_id.id
            inv.compute_taxes()
            inv._compute_amount()

        return True

# -*- coding: utf-8 -*-
from odoo import models, fields, api


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    ncf_dict = {
        "fiscal": "01",
        "final": "02",
        "gov": "15",
        "special": "14",
        "unico": '12',
        "debit_note": "03",
        "credit_note": "04"
    }

    ncf_control = fields.Boolean("Control de NCF", default=False)

    def get_next_char(self, number_next):
        sale_fiscal_type = self._context.get("sale_fiscal_type", False)
        if sale_fiscal_type:
            interpolated_prefix, interpolated_suffix = self._get_prefix_suffix()
            return interpolated_prefix + self.ncf_dict[
                sale_fiscal_type] + '%%0%sd' % self.padding % number_next + interpolated_suffix
        return super(IrSequence, self).get_next_char(number_next)

        interpolated_prefix, interpolated_suffix = self._get_prefix_suffix()
        return interpolated_prefix + '%%0%sd' % self.padding % number_next + interpolated_suffix

    def _next(self):
        """ Returns the next number in the preferred sequence in all the ones given in self."""
        sale_fiscal_type = self._context.get("sale_fiscal_type", False)
        if sale_fiscal_type:
            if not self.use_date_range:
                return self._next_do()
            # date mode
            dt = fields.Date.today()
            if self._context.get('ir_sequence_date'):
                dt = self._context.get('ir_sequence_date')

            seq_date = self.env['ir.sequence.date_range'].search(
                [('sale_fiscal_type', '=', sale_fiscal_type), ('sequence_id', '=', self.id), ('date_from', '<=', dt),
                 ('date_to', '>=', dt)], limit=1)
            if not seq_date:
                seq_date = self._create_date_range_seq(dt)
            return seq_date.with_context(ir_sequence_date_range=seq_date.date_from)._next()
        else:
            return super(IrSequence, self)._next()

    @api.multi
    def write(self, vals):
        if self._context.get("params", {}).get("model", {}) == "account.invoice":
            return True

        return super(IrSequence, self).write(vals)


class IrSequenceDateRange(models.Model):
    _inherit = 'ir.sequence.date_range'

    def get_sale_fiscal_type_from_partner(self):
        return self.env["res.partner"]._fields['sale_fiscal_type'].selection + [("credit_note", u"Nota de Crédito"),
                                                                                ("debit_note", u"Nota de Débito")]

    sale_fiscal_type = fields.Selection("get_sale_fiscal_type_from_partner",
                                        string="NCF para")
    max_number_next = fields.Integer(u"Número Máximo", default=100)

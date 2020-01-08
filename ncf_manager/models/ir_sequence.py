# © 2015-2018 Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 Gustavo Valverde <gustavo@iterativo.do>

# This file is part of NCF Manager.

# NCF Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# NCF Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with NCF Manager.  If not, see <https://www.gnu.org/licenses/>.

from odoo import models, fields, api


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    ncf_padding = fields.Integer(required=True,
                                 default=8,
                                 help="Padding legally use by NCF sequences")

    ncf_dict = {
        "fiscal": "01",
        "final": "02",
        "gov": "15",
        "special": "14",
        "unico": '12',
        "export": '16',
        "debit_note": "03",
        "credit_note": "04",
        "minor": "13",
        "informal": "11",
        "exterior": "17",
    }

    ncf_control = fields.Boolean("Control de NCF", default=False)

    def get_next_char(self, number_next):
        sale_fiscal_type = self._context.get("sale_fiscal_type", False)
        if sale_fiscal_type:
            return 'B' + self.ncf_dict[
                sale_fiscal_type] + '%%0%sd' % self.ncf_padding % number_next
        return super(IrSequence, self).get_next_char(number_next)

    def _next(self):
        """ Returns the next number in the preferred sequence in all the
         ones given in self."""
        sale_fiscal_type = self._context.get("sale_fiscal_type", False)
        dt = fields.Date.today()

        if sale_fiscal_type:
            if not self.use_date_range:
                return self._next_do()
            # date mode
            if self._context.get('ir_sequence_date'):
                dt = self._context.get('ir_sequence_date')

            seq_date = self.env['ir.sequence.date_range'].search(
                [('sale_fiscal_type', '=', sale_fiscal_type),
                 ('sequence_id', '=', self.id), ('date_from', '<=', dt),
                 ('date_to', '>=', dt)],
                limit=1)
            if not seq_date:
                seq_date = self._create_date_range_seq(dt)
            return seq_date.with_context(
                ir_sequence_date_range=seq_date.date_from)._next()
        else:
            # date mode
            if self._context.get('ir_sequence_date'):
                dt = self._context.get('ir_sequence_date')

            seq_date = self.env['ir.sequence.date_range'].search(
                [('sale_fiscal_type', '=', False),
                 ('sequence_id', '=', self.id), ('date_from', '<=', dt),
                 ('date_to', '>=', dt)],
                limit=1)
            if seq_date:
                return seq_date.with_context(
                    ir_sequence_date_range=seq_date.date_from)._next()
            return super(IrSequence, self)._next()

    @api.multi
    def write(self, vals):
        if self._context.get("params", {}).get("model",
                                               {}) == "account.invoice":
            return True

        return super(IrSequence, self).write(vals)


class IrSequenceDateRange(models.Model):
    _inherit = 'ir.sequence.date_range'

    def get_sale_fiscal_type_from_partner(self):
        return (self.env["res.partner"]._fields['sale_fiscal_type'].selection +
                [("credit_note", u"Nota de Crédito"),
                 ("debit_note", u"Nota de Débito"),
                 ("minor", "Gastos Menores"),
                 ("informal", "Comprobante de Compras"),
                 ("exterior", "Pagos al Exterior"),
                 ])

    sale_fiscal_type = fields.Selection("get_sale_fiscal_type_from_partner",
                                        string="NCF para")
    max_number_next = fields.Integer(u"Número Máximo", default=100)

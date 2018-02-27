from odoo import models, fields, _
from odoo.exceptions import UserError
from datetime import datetime
import pytz


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    ncf_control = fields.Boolean("Control de NCF", default=False)

    def _get_prefix_suffix(self):
        sale_fiscal_type = self._context.get("sale_fiscal_type", False)
        if sale_fiscal_type:
            def _interpolate(s, d):
                return (s % d) if s else ''

            def _interpolation_dict():
                now = range_date = effective_date = datetime.now(pytz.timezone(self._context.get('tz') or 'UTC'))
                if self._context.get('ir_sequence_date'):
                    effective_date = datetime.strptime(self._context.get('ir_sequence_date'), '%Y-%m-%d')
                if self._context.get('ir_sequence_date_range'):
                    range_date = datetime.strptime(self._context.get('ir_sequence_date_range'), '%Y-%m-%d')

                sequences = {
                    'year': '%Y', 'month': '%m', 'day': '%d', 'y': '%y', 'doy': '%j', 'woy': '%W',
                    'weekday': '%w', 'h24': '%H', 'h12': '%I', 'min': '%M', 'sec': '%S',
                    'sale_fiscal_type': '%sale_fiscal_type'
                }

                res = {}
                for key, format in sequences.items():
                    if key == 'sale_fiscal_type':
                        res[key] = sale_fiscal_type
                    else:
                        res[key] = effective_date.strftime(format)
                    res['range_' + key] = range_date.strftime(format)
                    res['current_' + key] = now.strftime(format)

                return res

            d = _interpolation_dict()
            try:
                interpolated_prefix = _interpolate(self.prefix, d)
                interpolated_suffix = _interpolate(self.suffix, d)
            except ValueError:
                raise UserError(_('Invalid prefix or suffix for sequence \'%s\'') % (self.get('name')))
            return interpolated_prefix, interpolated_suffix
        else:
            return super(IrSequence, self)._get_prefix_suffix()

    def _next(self):
        sale_fiscal_type = self._context.get("sale_fiscal_type", False)
        if sale_fiscal_type:
            """ Returns the next number in the preferred sequence in all the ones given in self."""
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


class IrSequenceDateRange(models.Model):
    _inherit = 'ir.sequence.date_range'

    sale_fiscal_type = fields.Selection(
        [("02", "Consumidor Final"),
         ("01", u"Crédito Fiscal"),
         ("15", "Gubernamental"),
         ("14", u"Regímenes Especiales"),
         ("13", u"Único ingreso")],
        string="NCF para")

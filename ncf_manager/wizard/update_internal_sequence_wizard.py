# -*- coding: utf-8 -*-
# ######################################################################
# © 2015-2018 Marcos Organizador de Negocios SRL. (https://marcos.do/)
#             Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 iterativo SRL. (https://iterativo.do/)
#             Gustavo Valverde <gustavo@iterativo.do>
# © 2017-2018 Neotec SRL. (https://neotec.do/)
#             Yasmany Castillo <yasmany003@gmail.do>

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
# along with NCF Manager.  If not, see <http://www.gnu.org/licenses/>.
# ######################################################################

from odoo import models, fields, api


class UpdateInternalSequenceWizard(models.TransientModel):
    _name = "update.internal.sequence.wizard"

    @api.model
    def _get_customer_prefix(self):
        sequence = self.env['ir.sequence'].search([
            ('code', '=', 'client.invoice.number')])
        return sequence.prefix

    @api.model
    def _get_customer_padding(self):
        sequence = self.env['ir.sequence'].search([
            ('code', '=', 'client.invoice.number')])
        return sequence.padding

    @api.model
    def _get_supplier_prefix(self):
        sequence = self.env['ir.sequence'].search([
            ('code', '=', 'supplier.invoice.number')])
        return sequence.prefix

    @api.model
    def _get_supplier_padding(self):
        sequence = self.env['ir.sequence'].search([
            ('code', '=', 'supplier.invoice.number')])
        return sequence.padding

    @api.model
    def _get_debit_note_prefix(self):
        sequence = self.env['ir.sequence'].search([
            ('code', '=', 'debit.note.invoice.number')])
        return sequence.prefix

    @api.model
    def _get_debit_note_padding(self):
        sequence = self.env['ir.sequence'].search([
            ('code', '=', 'debit.note.invoice.number')])
        return sequence.padding

    @api.model
    def _get_credit_note_prefix(self):
        sequence = self.env['ir.sequence'].search([
            ('code', '=', 'credit.note.invoice.number')])
        return sequence.prefix

    @api.model
    def _get_credit_note_padding(self):

        seq = self.env['ir.sequence'].search([
            ('code', '=', 'credit.note.invoice.number')])
        return seq.padding

    customer_prefix = fields.Char(
        string="Prefijo Sec. Cliente", default=_get_customer_prefix)
    customer_padding = fields.Integer(
        string="Longitud Numeración", default=_get_customer_padding)
    supplier_prefix = fields.Char(
        string="Prefijo Sec. Proveedor", default=_get_supplier_prefix)
    supplier_padding = fields.Integer(
        string="Longitud Numeración", default=_get_supplier_padding)
    debit_note_prefix = fields.Char(
        string="Prefijo Secuencia ND", default=_get_debit_note_prefix)
    debit_note_padding = fields.Integer(
        string="Longitud Numeración", default=_get_debit_note_padding)
    credit_note_prefix = fields.Char(
        string="Prefijo Secuencia NC", default=_get_credit_note_prefix)
    credit_note_padding = fields.Integer(
        string="Longitud Numeración", default=_get_credit_note_padding)

    @api.multi
    def update_sequences(self):
        sequence = self.env['ir.sequence']

        if self.customer_prefix or self.customer_padding:
            customer_seq = sequence.search([
                ('code', '=', 'client.invoice.number')])
            customer_seq.write({
                'prefix': self.customer_prefix,
                'padding': self.customer_padding,
            })

        if self.supplier_prefix or self.supplier_padding:
            supplier_seq = sequence.search([
                ('code', '=', 'supplier.invoice.number')])
            supplier_seq.write({
                'prefix': self.supplier_prefix,
                'padding': self.supplier_padding,
            })

        if self.debit_note_prefix or self.debit_note_padding:
            debit_note_seq = sequence.search([
                ('code', '=', 'debit.note.invoice.number')])
            debit_note_seq.write({
                'prefix': self.debit_note_prefix,
                'padding': self.debit_note_padding,
            })

        if self.credit_note_prefix or self.credit_note_padding:
            credit_note_seq = sequence.search([
                ('code', '=', 'credit.note.invoice.number')])
            credit_note_seq.write({
                'prefix': self.credit_note_prefix,
                'padding': self.credit_note_padding,
            })

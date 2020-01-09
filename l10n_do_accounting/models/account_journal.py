# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, RedirectWarning


class AccountJournal(models.Model):

    _inherit = 'account.journal'

    l10n_do_payment_form = fields.Selection(
        [('cash', 'Cash'),
         ('bank', 'Check / Transfer'),
         ('card', 'Credit Card'),
         ('credit', 'Credit'),
         ('swap', 'Swap'),
         ('bond', 'Bonds or Gift Certificate'),
         ('others', 'Other Sale Type')],
        string='Payment Form',
    )

    l10n_do_sequence_ids = fields.One2many('ir.sequence', 'l10n_latam_journal_id', string='Sequences')

    def _get_journal_sequence(self, counterpart_partner=False):
        """ Regarding the DGII responsibility of the company and the type of journal (sale/purchase), get the allowed
        sequences. Optionally, receive the counterpart partner (customer/supplier) and get the allowed sequences to work
        with him. This method is used to populate document types on journals and also to filter document types on
        specific invoices to/from customer/supplier
        """
        self.ensure_one()
        sequences_data = {
            'issued': {
                'B': ['01', '02', '11', '13'],
            },
            'received': {
                'B': ['01'],
            },
        }
        if not self.company_id.vat:
            action = self.env.ref('base.action_res_company_form')
            msg = _('Can not create chart of account until you configure your company VAT.')
            raise RedirectWarning(msg, action.id, _('Go to Companies'))

        sequences = sequences_data['issued' if self.type == 'sale' else 'received'][
            self.company_id.l10n_do_dgii_responsibility_type_id.code]
        if not counterpart_partner:
            return sequences
        else:
            counterpart_sequences = sequences_data['issued' if self.type == 'purchase' else 'received'][
                counterpart_partner.l10n_do_dgii_responsibility_type_id.code]
            sequences = list(set(sequences) & set(counterpart_sequences))
        return sequences

    def _get_journal_codes(self):
        self.ensure_one()
        usual_codes = ['1', '2', '3', '6', '7', '8', '11', '12', '13']
        mipyme_codes = ['201', '202', '203', '206', '207', '208', '211', '212', '213']
        invoice_m_code = ['51', '52', '53']
        receipt_m_code = ['54']
        receipt_codes = ['4', '9', '15']
        expo_codes = ['19', '20', '21']
        if self.type != 'sale':
            return []
        elif self.l10n_ar_afip_pos_system == 'II_IM':
            # pre-printed invoice
            return usual_codes + receipt_codes + expo_codes + invoice_m_code + receipt_m_code
        elif self.l10n_ar_afip_pos_system in ['RAW_MAW', 'RLI_RLM']:
            # electronic/online invoice
            return usual_codes + receipt_codes + invoice_m_code + receipt_m_code + mipyme_codes
        elif self.l10n_ar_afip_pos_system in ['CPERCEL', 'CPEWS']:
            # invoice with detail
            return usual_codes + invoice_m_code
        elif self.l10n_ar_afip_pos_system in ['BFERCEL', 'BFEWS']:
            # Bonds invoice
            return usual_codes + mipyme_codes
        elif self.l10n_ar_afip_pos_system in ['FEERCEL', 'FEEWS', 'FEERCELP']:
            return expo_codes

    @api.model
    def create(self, values):
        """ Create Document sequences after create the journal """
        res = super().create(values)
        res._l10n_do_create_document_sequences()
        return res

    def write(self, values):
        """ Update Document sequences after update journal """
        to_check = set(['type', 'l10n_do_share_sequences', 'l10n_latam_use_documents'])
        res = super().write(values)
        if to_check.intersection(set(values.keys())):
            for rec in self:
                rec._l10n_do_create_document_sequences()
        return res

    @api.constrains('type', 'l10n_do_dgii_pos_number', 'l10n_do_share_sequences',
                    'l10n_latam_use_documents')
    def _check_dgii_configurations(self):
        """ Do not let to update journal if already have confirmed invoices """
        self.ensure_one()
        if self.company_id.country_id != self.env.ref('base.do'):
            return True
        if self.type != 'sale' and self._origin.type != 'sale':
            return True
        invoices = self.env['account.move'].search([('journal_id', '=', self.id), ('state', '!=', 'draft')])
        if invoices:
            raise ValidationError(_(
                'You can not change the journal configuration for a journal that already have validate invoices') +
                ':<br/><br/> - %s' % ('<br/>- '.join(invoices.mapped('display_name'))))

    def _l10n_do_create_document_sequences(self):
        """ IF DGII Configuration change try to review if this can be done and then create / update the document
        sequences """
        self.ensure_one()
        if self.company_id.country_id != self.env.ref('base.do'):
            return True
        if not self.type == 'sale' or not self.l10n_latam_use_documents:
            return False

        sequences = self.l10n_do_sequence_ids
        sequences.unlink()

        # Create Sequences
        sequences = self._get_journal_sequence()
        internal_types = ['invoice', 'debit_note', 'credit_note']
        domain = [('country_id.code', '=', 'DO'),
                  ('internal_type', 'in', internal_types),
                  '|',
                  ('l10n_do_sequence', '=', False),
                  ('l10n_do_sequence', 'in', sequences)]
        documents = self.env['l10n_latam.document.type'].search(domain)
        for document in documents:
            sequences |= self.env['ir.sequence'].create(document._get_document_sequence_vals(self))
        return sequences

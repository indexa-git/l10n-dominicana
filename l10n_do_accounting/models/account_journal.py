from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, RedirectWarning


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def _get_l10n_do_payment_form(self):
        """ Return the list of payment forms allowed by DGII. """
        return [
            ('cash', _('Cash')),
            ('bank', _('Check / Transfer')),
            ('card', _('Credit Card')),
            ('credit', _('Credit')),
            ('swap', _('Swap')),
            ('bond', _('Bonds or Gift Certificate')),
            ('others', _('Other Sale Type')),
        ]

    l10n_do_payment_form = fields.Selection(
        selection='_get_l10n_do_payment_form', string='Payment Form',
    )
    l10n_do_sequence_ids = fields.One2many(
        'ir.sequence', 'l10n_latam_journal_id', string='Sequences',
    )

    def _get_journal_ncf_types(self, counterpart_partner=False, invoice=False):
        """
        Regarding the DGII type of company and the type of journal
        (sale/purchase), get the allowed NCF types. Optionally, receive
        the counterpart partner (customer/supplier) and get the allowed
        NCF types to work with him. This method is used to populate
        document types on journals and also to filter document types on
        specific invoices to/from customer/supplier
        """
        self.ensure_one()
        ncf_types_data = {
            'issued': {
                'taxpayer': ['fiscal'],
                'non_payer': ['consumer', 'unique'],
                'nonprofit': ['fiscal'],
                'special': ['special'],
                'governmental': ['governmental'],
                'foreigner': ['export', 'consumer'],
            },
            'received': {
                'taxpayer': ['fiscal', 'special', 'governmental'],
                'non_payer': ['informal', 'minor'],
                'nonprofit': ['special', 'governmental'],
                'special': ['fiscal', 'special', 'governmental'],
                'governmental': ['fiscal', 'special', 'governmental'],
                'foreigner': ['import', 'exterior'],
            },
        }
        if not self.company_id.vat:
            action = self.env.ref('base.action_res_company_form')
            msg = _('Cannot create chart of account until you configure your VAT.')
            raise RedirectWarning(msg, action.id, _('Go to Companies'))

        # Get all the ncf_types values from the nested dictionary, remove duplicates and
        # convert it into a list
        ncf_types = list(
            set(
                [
                    value
                    for dic in ncf_types_data[
                        'issued' if self.type == 'sale' else 'received'
                    ].values()
                    for value in dic
                ]
            )
        )
        if not counterpart_partner:
            ncf_notes = list(['fiscal', 'debit_note', 'credit_note'])
            ncf_external = list(['fiscal', 'special', 'governmental'])
            return (
                ncf_types + ncf_notes
                if self.type == 'sale'
                else [ncf for ncf in ncf_types if ncf not in ncf_external]
            )
        else:
            counterpart_ncf_types = ncf_types_data[
                'issued' if self.type == 'sale' else 'received'
            ][counterpart_partner.l10n_do_dgii_tax_payer_type]
            ncf_types = list(set(ncf_types) & set(counterpart_ncf_types))
        if invoice.type in ['out_refund', 'in_refund']:
            ncf_types = ['credit_note']
        if invoice._compute_is_debit_note() or \
                self.env.context.get('internal_type') == 'debit_note':
            ncf_types = ['debit_note']
        return ncf_types

    def _get_journal_codes(self):
        self.ensure_one()
        ncf_code = ['B']
        # ecf_code = ['E'] # Needs better logic
        if self.type != 'sale':
            return []
        # elif self.company_id.l10n_do_ecf_issuer:
        #     return ecf_code
        return ncf_code

    @api.model
    def create(self, values):
        """ Create Document sequences after create the journal """
        res = super().create(values)
        res._l10n_do_create_document_sequences()
        return res

    def write(self, values):
        """ Update Document sequences after update journal """
        to_check = {'type', 'l10n_latam_use_documents'}
        res = super().write(values)
        if to_check.intersection(set(values.keys())):
            for rec in self:
                rec._l10n_do_create_document_sequences()
        return res

    @api.constrains(
        'type', 'l10n_latam_use_documents',
    )
    def _check_dgii_configurations(self):
        """ Do not let to update journal if already have confirmed invoices """
        self.ensure_one()
        if self.company_id.country_id != self.env.ref('base.do'):
            return True
        if self.type != 'sale' and self._origin.type != 'sale':
            return True
        invoices = self.env['account.move'].search(
            [('journal_id', '=', self.id), ('state', '!=', 'draft')]
        )
        if invoices:
            raise ValidationError(
                _(
                    'You can not change the journal configuration for a '
                    'journal that already have validate invoices'
                )
                + ':<br/><br/> - %s' % ('<br/>- '.join(invoices.mapped('display_name')))
            )

    def _l10n_do_create_document_sequences(self):
        """ IF DGII Configuration changes try to review if this can be done
        and then create / update the document sequences """
        self.ensure_one()
        if self.company_id.country_id != self.env.ref('base.do'):
            return True
        if not self.l10n_latam_use_documents:
            return False

        sequences = self.l10n_do_sequence_ids
        sequences.unlink()

        # Create Sequences
        ncf_types = self._get_journal_ncf_types()
        internal_types = ['invoice', 'in_invoice', 'debit_note', 'credit_note']
        domain = [
            ('country_id.code', '=', 'DO'),
            ('internal_type', 'in', internal_types),
            ('active', '=', True),
            "|",
            ("l10n_do_ncf_type", "=", False),
            ('l10n_do_ncf_type', 'in', ncf_types),
        ]
        documents = self.env['l10n_latam.document.type'].search(domain)
        for document in documents:
            sequences |= self.env['ir.sequence'].create(
                document._get_document_sequence_vals(self)
            )
        return sequences

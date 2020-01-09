from odoo import models, api, fields, _
from odoo.exceptions import UserError


class L10nLatamDocumentType(models.Model):

    _inherit = 'l10n_latam.document.type'

    l10n_do_sequence = fields.Selection(
        selection='_get_l10n_do_sequences',
        string='Sequences',
        help='Sequences defined by the DGII that can be used to identify the'
        ' documents presented to the government and that depends on the'
        ' operation type, the responsibility of both the issuer and the'
        ' receptor of the document')
    purchase_aliquots = fields.Selection(
        [('not_zero', 'Not Zero'), ('zero', 'Zero')],
        help='Raise an error if a vendor bill is miss encoded. "Not Zero"'
        ' means the VAT taxes are required for the invoices related to this document type, and those with "Zero" means'
        ' that only "VAT Not Applicable" tax is allowed.')

    def _get_l10n_do_sequences(self):
        """ Return the list of values of the selection field. """
        return [
            ('fiscal', '01'),
            ('consumer', '02'),
            ('debit_note', '03'),
            ('credit_note', '04'),
            ('informal', '11'),
            ('unique', '12'),
            ('minor', '13'),
            ('special', '14'),
            ('goverment', '15'),
            ('export', '16'),
            ('exterior', '17'),

        ]

    def _get_document_sequence_vals(self, journal):
        """ Values to create the sequences """
        values = super()._get_document_sequence_vals(journal)
        if self.country_id != self.env.ref('base.do'):
            return values

        values.update({
            'padding': 8,
            'implementation': 'no_gap',
            'prefix': journal.l10n_do_dgii_pos_number, # TODO: Use 
            'l10n_latam_journal_id': journal.id
        })
        # if journal.l10n_do_share_sequences:
        #     values.update({
        #         'name': '%s - Sequence %s Documents' %
        #                 (journal.name, self.l10n_do_sequence),
        #         'l10n_do_sequence': self.l10n_do_sequence
        #     })
        # else:
        #     values.update({
        #         'name': '%s - %s' % (journal.name, self.name),
        #         'l10n_latam_document_type_id': self.id
        #     })
        return values

    def _filter_taxes_included(self, taxes):
        """ In argentina we include taxes depending on document sequence """
        self.ensure_one()
        if self.country_id == self.env.ref(
                'base.do') and self.l10n_do_sequence in ['fiscal', 'informal']:
            return taxes.filtered(
                lambda x: x.tax_group_id.l10n_do_vat_dgii_code)
        return super()._filter_taxes_included(taxes)

    def _format_document_number(self, document_number):
        """ Make validation of Import Dispatch Number
          * making validations on the document_number. If it is wrong it should raise an exception
          * format the document_number against a pattern and return it
        """
        self.ensure_one()
        if self.country_id != self.env.ref('base.do'):
            return super()._format_document_number(document_number)

        if not document_number:
            return False

        msg = "'%s' " + _("is not a valid value for") + " '%s'.<br/>%s"

        # Import Dispatch Number Validator
        if self.code == 'E':
            if len(document_number) != 16:
                raise UserError(msg % (document_number, self.name, _('The number of import Dispatch must be 16 characters')))
            return document_number

        # Invoice Number Validator (For Eg: 123-123)
        failed = False
        args = document_number.split('-')
        if len(args) != 2:
            failed = True
        else:
            pos, number = args
            if len(pos) > 5 or not pos.isdigit():
                failed = True
            elif len(number) > 8 or not number.isdigit():
                failed = True
            if len(pos) == 5 and pos[0] == '0':
                pos = pos[1:]
            document_number = '{:>04s}-{:>08s}'.format(pos, number)
        if failed:
            raise UserError(msg % (document_number, self.name, _(
                'The document number must be entered with a dash (-) and a maximum of 5 characters for the first part'
                'and 8 for the second. The following are examples of valid numbers:\n* 1-1\n* 0001-00000001'
                '\n* 00001-00000001')))

        return document_number

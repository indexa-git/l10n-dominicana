import logging

from odoo import models, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from stdnum.do.ncf import is_valid
except (ImportError, IOError) as err:
    _logger.debug(err)


class L10nLatamDocumentType(models.Model):

    _inherit = 'l10n_latam.document.type'

    l10n_do_sequence = fields.Selection(
        selection='_get_l10n_do_sequences',
        string='Sequences',
        help='Sequences defined by the DGII that can be used to identify the'
        ' documents presented to the government and that depends on the'
        ' operation type, the responsibility of both the issuer and the'
        ' receptor of the document',
    )

    purchase_vat = fields.Selection(
        [('not_zero', 'Not Zero'), ('zero', 'Zero')],
        help='Raise an error if a vendor bill is miss encoded. "Not Zero"'
        ' means the VAT taxes are required for the invoices related to this document type, and those with "Zero" means'
        ' that only "VAT Not Applicable" tax is allowed.',
    )

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
            ('governmental', '15'),
            ('export', '16'),
            ('exterior', '17'),
            ('e-fiscal', '31'),
            ('e-consumer', '32'),
            ('e-debit_note', '33'),
            ('e-credit_note', '34'),
            ('e-informal', '41'),
            ('e-minor', '43'),
            ('e-special', '44'),
            ('e-governmental', '45'),
        ]

    def _get_document_sequence_vals(self, journal):
        """ Values to create the sequences """
        values = super()._get_document_sequence_vals(journal)
        if self.country_id != self.env.ref('base.do'):
            return values

        values.update(
            {
                'padding': 8,
                'implementation': 'no_gap',
                'prefix': self.doc_code_prefix,
                'l10n_latam_document_type_id': self.id,
                'l10n_latam_journal_id': journal.id,
            }
        )
        return values

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
        if not is_valid(document_number):
            raise UserError(
                msg
                % (
                    document_number,
                    self.name,
                    _('Please check the number and try again'),
                )
            )
        return document_number
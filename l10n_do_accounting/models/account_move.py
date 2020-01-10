# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):

    _inherit = 'account.move'

    l10n_latam_internal_type = fields.Selection(
        related='l10n_latam_document_type_id.internal_type'
    )

    l10n_do_partner_type = fields.Selection(
        related='res_partner.l10n_do_dgii_tax_payer_type'
    )

    is_debit_note = fields.Boolean()

    def _get_l10n_latam_documents_domain(self):
        self.ensure_one()
        domain = super()._get_l10n_latam_documents_domain()
        if (
            self.journal_id.l10n_latam_use_documents
            and self.journal_id.company_id.country_id == self.env.ref('base.do')
        ):
            ncf_types = self.journal_id._get_journal_ncf_types(
                counterpart_partner=self.partner_id.commercial_partner_id, invoice=self,
            )
            domain += [
                '|',
                ('l10n_do_ncf_type', '=', False),
                ('l10n_do_ncf_type', 'in', ncf_types),
            ]
            codes = self.journal_id._get_journal_codes()
            if codes:
                domain.append(('code', 'in', codes))
        return domain

    def _get_document_type_sequence(self):
        """ Return the match sequences for the given journal and invoice """
        self.ensure_one()
        if (
            self.journal_id.l10n_latam_use_documents
            and self.l10n_latam_country_code == 'DO'
        ):
            res = self.journal_id.l10n_do_sequence_ids.filtered(
                lambda x: x.l10n_latam_document_type_id
                == self.l10n_latam_document_type_id
            )
            return res
        return super()._get_document_type_sequence()

    @api.constrains('type', 'l10n_latam_document_type_id')
    def _check_invoice_type_document_type(self):
        super()._check_invoice_type_document_type()
        for rec in self.filtered(
            lambda r: r.company_id.country_id == self.env.ref('base.do')
            and r.l10n_latam_document_type_id
        ):
            tax_payer_type = rec.partner_id.l10n_do_dgii_tax_payer_type
            latam_document_type_code = (
                rec.l10n_latam_document_type_id.l10n_do_ncf_type
            )
            if not tax_payer_type and latam_document_type_code not in [
                '01',
                '03',
                '04',
                '14',
                '15',
            ]:
                raise ValidationError(
                    _(
                        'Tax payer type is mandatory for this type of document. '
                        'Please set the current tax payer type of this client'
                    )
                )

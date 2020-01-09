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

    def _get_l10n_latam_documents_domain(self):
        self.ensure_one()
        domain = super()._get_l10n_latam_documents_domain()
        if (
            self.journal_id.l10n_latam_use_documents
            and self.journal_id.company_id.country_id == self.env.ref('base.do')
        ):
            sequences = self.journal_id._get_journal_sequence(
                counterpart_partner=self.partner_id.commercial_partner_id
            )
            domain += [
                '|',
                ('l10n_do_sequence', '=', False),
                ('l10n_do_sequence', 'in', sequences),
            ]
            codes = self.journal_id._get_journal_codes()
            if codes:
                domain.append(('code', 'in', codes))
        return domain

    def _get_l10n_latam_documents_domain(self):
        self.ensure_one()
        domain = super()._get_l10n_latam_documents_domain()
        if (
            self.journal_id.l10n_latam_use_documents
            and self.journal_id.company_id.country_id == self.env.ref('base.cl')
        ):
            if self.type in ['in_invoice', 'in_refund']:
                domain += [('code', 'in', ['35', '38', '39', '41', '56', '61'])]
            return domain
            document_type_ids = self.journal_id.l10n_cl_sequence_ids.mapped(
                'l10n_latam_document_type_id'
            ).ids
            domain += [('id', 'in', document_type_ids)]
            if self.partner_id.l10n_cl_sii_taxpayer_type == '3':
                domain += [('code', 'in', ['35', '38', '39', '41', '56', '61'])]
        return domain

    def _get_document_type_sequence(self):
        """ Return the match sequences for the given journal and invoice """
        self.ensure_one()
        if (
            self.journal_id.l10n_latam_use_documents
            and self.l10n_latam_country_code == 'CL'
        ):
            res = self.journal_id.l10n_cl_sequence_ids.filtered(
                lambda x: x.l10n_latam_document_type_id
                == self.l10n_latam_document_type_id
            )
            return res
        return super()._get_document_type_sequence()

    @api.constrains('type', 'l10n_latam_document_type_id')
    def _check_invoice_type_document_type(self):
        super()._check_invoice_type_document_type()
        for rec in self.filtered(
            lambda r: r.company_id.country_id == self.env.ref('base.cl')
            and r.l10n_latam_document_type_id
        ):
            tax_payer_type = rec.partner_id.l10n_cl_sii_taxpayer_type
            latam_document_type_code = rec.l10n_latam_document_type_id.code
            if not tax_payer_type and latam_document_type_code not in [
                '35',
                '38',
                '39',
                '41',
            ]:
                raise ValidationError(
                    _(
                        'Tax payer type is mandatory for this type of document. '
                        'Please set the current tax payer type of this client'
                    )
                )
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_l10n_do_annulment_type(self):
        """ Return the list of annulment types required by DGII. """
        return [
            ('01', _('01 - Pre-printed Invoice Impairment')),
            ('02', _('02 - Printing Errors (Pre-printed Invoice)')),
            ('03', _('03 - Defective Printing')),
            ('04', _('04 - Correction of Product Information')),
            ('05', _('05 - Product Change')),
            ('06', _('06 - Product Return')),
            ('07', _('07 - Product Omission')),
            ('08', _('08 - NCF Sequence Errors')),
            ('09', _('09 - For Cessation of Operations')),
            ('10', _('10 - Lossing or Hurting Of Counterfoil')),
        ]

    l10n_do_annulment_type = fields.Selection(
        selection='_get_l10n_do_annulment_type', string='Annulment Type', copy=False,
    )

    l10n_latam_document_number = fields.Char(store=True)

    def _is_debit_note(self):
        self.ensure_one()
        if (
            self.journal_id.l10n_latam_use_documents
            and self.journal_id.company_id.country_id == self.env.ref('base.do')
            and self.type == 'out_invoice'
            and self.ref
        ):
            return True if self.ref[-10:-8] == '03' else False

    @api.depends('name')
    def _compute_l10n_latam_document_number(self):
        recs_with_name = self.filtered(lambda x: x.name != '/')
        for rec in recs_with_name:
            name = rec.name
            doc_code_prefix = rec.l10n_latam_document_type_id.doc_code_prefix
            if doc_code_prefix and name:
                name = name.split(" ", 1)[-1]
            rec.l10n_latam_document_number = rec.l10n_latam_document_number
        remaining = self - recs_with_name
        remaining.l10n_latam_document_number = False

    @api.onchange('l10n_latam_document_type_id', 'l10n_latam_document_number')
    def _inverse_l10n_latam_document_number(self):
        moves = self.filtered(lambda m: m.l10n_latam_country_code != 'DO')

        for rec in moves.filtered('l10n_latam_document_type_id'):
            if not rec.l10n_latam_document_number:
                rec.name = '/'
            else:
                l10n_latam_document_number = rec.l10n_latam_document_type_id._format_document_number(rec.l10n_latam_document_number)
                if rec.l10n_latam_document_number != l10n_latam_document_number:
                    rec.l10n_latam_document_number = l10n_latam_document_number

        super(AccountMove, moves)._inverse_l10n_latam_document_number()

    def _get_l10n_latam_documents_domain(self):
        self.ensure_one()
        domain = super()._get_l10n_latam_documents_domain()
        if (
            self.journal_id.l10n_latam_use_documents
            and self.journal_id.company_id.country_id == self.env.ref('base.do')
        ):
            ncf_types = self.journal_id._get_journal_ncf_types(
                counterpart_partner=self.partner_id.commercial_partner_id, invoice=self
            )
            domain += [
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
            latam_document_type_code = rec.l10n_latam_document_type_id.l10n_do_ncf_type
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

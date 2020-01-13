from odoo import models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def post(self):
        for rec in self.filtered(
            lambda x: x.l10n_latam_use_documents and (not x.name or x.name == '/')
        ):
            if not rec.l10n_latam_sequence_id:
                raise UserError(
                    _('No sequence or document number linked to invoice id %s') % rec.id
                )
            if rec.type in ('in_receipt', 'out_receipt'):
                raise UserError(
                    _('We do not accept the usage of document types on receipts yet. ')
                )
            if not rec.l10n_latam_document_number:

                doc_pool_id = self.env['l10n_latam.document.pool'].search(
                    [
                        (
                            'l10n_latam_document_type_id',
                            '=',
                            rec.l10n_latam_document_type_id.id,
                        ),
                        ('state', '=', 'active'),
                    ]
                )

                rec.l10n_latam_document_number = (
                    doc_pool_id.get_fiscal_number() if doc_pool_id else ""
                )
        return super().post()

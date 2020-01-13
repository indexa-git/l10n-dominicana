# TODO: poner authorship en todos los archivos .py (xml tamb?)

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class L10nLatamDocumentPoolValidateWizard(models.TransientModel):
    """
    This Wizard purpose is to warn the user when attempt to change
    sequence state.
    """
    _name = 'l10n_latam.document.pool.validate_wizard'
    _description = 'Account Fiscal Sequence Validate Wizard'

    name = fields.Char()
    l10n_latam_sequence_id = fields.Many2one(
        'l10n_latam.document.pool',
        string='Fiscal sequence',
    )

    def confirm_cancel(self):
        self.ensure_one()
        if self.l10n_latam_sequence_id:
            action = self._context.get('action', False)
            if action == 'confirm':
                self.l10n_latam_sequence_id._action_confirm()
            elif action == 'cancel':
                self.l10n_latam_sequence_id._action_cancel()
        else:
            raise ValidationError(
                _("There is no Fiscal Sequence to perform this action."))

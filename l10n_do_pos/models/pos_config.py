from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PosConfig(models.Model):
    _inherit = "pos.config"

    l10n_do_default_partner_id = fields.Many2one(
        "res.partner",
        string="Default partner",
    )
    l10n_do_order_loading_options = fields.Selection(
        [
            ("current_session", "Load current session orders"),
            ("n_days", "Load last 'n' days orders"),
        ],
        default="current_session",
        string="Loading options",
    )
    l10n_do_number_of_days = fields.Integer(
        string="Last Days (invoices)",
        default=10,
    )
    l10n_latam_use_documents = fields.Boolean(
        related="invoice_journal_id.l10n_latam_use_documents",
    )
    l10n_do_credit_notes_number_of_days = fields.Integer(
        string="Last Days (refunds)",
        default=10,
    )
    l10n_latam_country_code = fields.Char(
        related="company_id.country_id.code",
        help="Technical field used to hide/show fields regarding the localization",
    )

    # TODO: search criteria
    # order_search_criteria = fields.Many2many(
    #     comodel_name='pos.search_criteria',
    #     string=u"Criterios de Búsqueda",
    # )

    @api.constrains("l10n_do_number_of_days")
    def l10n_do_number_of_days_validation(self):
        if self.l10n_do_order_loading_options == "n_days" and (
            not self.l10n_do_number_of_days or self.l10n_do_number_of_days < 0
        ):
            raise UserError(_("You have to set a number of days."))

    def get_l10n_do_fiscal_type_data(self):
        return {
            "tax_payer_type_list": [
                self.env["res.partner"]._get_l10n_do_dgii_payer_types_selection()[i]
                for i in [1, 0, 2, 3, 4, 5]
            ],
            "ncf_types_data": self.env["account.journal"]._get_l10n_do_ncf_types_data(),
        }

    @api.constrains("company_id", "journal_id")
    def _check_company_journal(self):
        if (
            self.journal_id
            and self.journal_id.company_id.l10n_do_country_code == "DO"
            and self.journal_id.l10n_latam_use_documents
        ):
            raise ValidationError(
                _(
                    "You cannot set a Fiscal Journal as Sales Journal. "
                    "Please, select a non-fiscal journal."
                )
            )
        super(PosConfig, self)._check_company_journal()

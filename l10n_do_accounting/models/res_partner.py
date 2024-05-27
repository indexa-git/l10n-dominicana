from odoo import models, fields, api, _
from odoo.exceptions import AccessError


class Partner(models.Model):
    _inherit = "res.partner"

    def _get_l10n_do_dgii_payer_types_selection(self):
        """Return the list of payer types needed in invoices to clasify accordingly to
        DGII requirements."""
        return [
            ("taxpayer", _("Fiscal Tax Payer")),
            ("non_payer", _("Non Tax Payer")),
            ("nonprofit", _("Nonprofit Organization")),
            ("special", _("special from Tax Paying")),
            ("governmental", _("Governmental")),
            ("foreigner", _("Foreigner")),
        ]

    def _get_l10n_do_expense_type(self):
        """Return the list of expenses needed in invoices to clasify accordingly to
        DGII requirements."""
        return [
            ("01", _("01 - Personal")),
            ("02", _("02 - Work, Supplies and Services")),
            ("03", _("03 - Leasing")),
            ("04", _("04 - Fixed Assets")),
            ("05", _("05 - Representation")),
            ("06", _("06 - Admitted Deductions")),
            ("07", _("07 - Financial Expenses")),
            ("08", _("08 - Extraordinary Expenses")),
            ("09", _("09 - Cost & Expenses part of Sales")),
            ("10", _("10 - Assets Acquisitions")),
            ("11", _("11 - Insurance Expenses")),
        ]

    l10n_do_dgii_tax_payer_type = fields.Selection(
        selection="_get_l10n_do_dgii_payer_types_selection",
        compute="_compute_l10n_do_dgii_payer_type",
        inverse="_inverse_l10n_do_dgii_tax_payer_type",
        string="Taxpayer Type",
        index=True,
        store=True,
    )
    l10n_do_expense_type = fields.Selection(
        selection="_get_l10n_do_expense_type",
        string="Cost & Expense Type",
        store=True,
    )
    country_id = fields.Many2one(
        default=lambda self: self.env.ref("base.do")
        if self.env.user.company_id.country_id == self.env.ref("base.do")
        else False
    )

    def _check_l10n_do_fiscal_fields(self, vals):
        if not self or self.parent_id:
            # Do not perform any check because child contacts
            # have readonly fiscal field. This also allows set
            # contacts parent, even if this changes any of its
            # fiscal fields.
            return

        fiscal_fields = [
            field
            for field in ["name", "vat", "country_id"]  # l10n_do_dgii_tax_payer_type ?
            if field in vals
        ]
        if (
            fiscal_fields
            and not self.env.user.has_group(
                "l10n_do_accounting.group_l10n_do_edit_fiscal_partner"
            )
            and self.env["account.move"]
            .sudo()
            .search(
                [
                    ("l10n_latam_use_documents", "=", True),
                    ("country_code", "=", "DO"),
                    ("commercial_partner_id", "=", self.id),
                    ("state", "=", "posted"),
                ],
                limit=1,
            )
        ):
            raise AccessError(
                _(
                    "You are not allowed to modify %s after partner "
                    "fiscal document issuing"
                )
                % (", ".join(self._fields[f].string for f in fiscal_fields))
            )

    def write(self, vals):
        res = super(Partner, self).write(vals)
        self._check_l10n_do_fiscal_fields(vals)

        return res

    @api.depends("vat", "country_id", "name")
    def _compute_l10n_do_dgii_payer_type(self):
        """Compute the type of partner depending on soft decisions"""
        for partner in self:
            vat = partner.vat or partner.name or ""
            vat_len = len(vat) if vat else 0
            upper_name = partner.name.upper() if partner.name else ""
            is_dominican_partner = partner.country_code == "DO"

            if not is_dominican_partner:
                partner.l10n_do_dgii_tax_payer_type = "foreigner"
                continue

            if not vat.isdigit():
                partner.l10n_do_dgii_tax_payer_type = "non_payer"
                continue

            if vat_len == 11:
                partner.l10n_do_dgii_tax_payer_type = "non_payer"
            elif vat_len == 9:
                if "MINISTERIO" in upper_name and not vat.startswith("4"):
                    partner.l10n_do_dgii_tax_payer_type = "governmental"
                elif "ZONA FRANCA" in upper_name:
                    partner.l10n_do_dgii_tax_payer_type = "special"
                elif "IGLESIA" in upper_name or (
                    "MINISTERIO" in upper_name and vat.startswith("4")
                ):
                    partner.l10n_do_dgii_tax_payer_type = "special"
                elif not vat.startswith("4"):
                    partner.l10n_do_dgii_tax_payer_type = "taxpayer"
                else:
                    partner.l10n_do_dgii_tax_payer_type = "nonprofit"
            else:
                partner.l10n_do_dgii_tax_payer_type = "non_payer"

    def _inverse_l10n_do_dgii_tax_payer_type(self):
        for partner in self:
            partner.l10n_do_dgii_tax_payer_type = partner.l10n_do_dgii_tax_payer_type

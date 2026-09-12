from odoo import models, fields, api, _
from odoo.exceptions import AccessError

# Xml id, without company prefix, of the "Regimenes Especiales" fiscal position
# created by the Dominican chart of accounts on every company.
SPECIAL_FISCAL_POSITION_XMLID = "position_especial"


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

    @api.model
    def _l10n_do_get_special_fiscal_position(self):
        """Get the "Regimenes Especiales" fiscal position of the active company.

        The Dominican chart of accounts creates one fiscal position per company,
        so it is looked up through its company prefixed xml id. Databases coming
        from previous versions keep that record under the ``l10n_do`` module.

        Returns:
            account.fiscal.position: the fiscal position, empty recordset if the
                Dominican chart of accounts is not installed on the company.
        """
        fiscal_position = self.env["account.chart.template"].ref(
            SPECIAL_FISCAL_POSITION_XMLID, raise_if_not_found=False
        ) or self.env.ref(
            f"l10n_do.{self.env.company.id}_{SPECIAL_FISCAL_POSITION_XMLID}",
            raise_if_not_found=False,
        )

        return fiscal_position or self.env["account.fiscal.position"]

    def _l10n_do_set_special_fiscal_position(self):
        """Set the "Regimenes Especiales" fiscal position on exempt partners.

        Partners which already have a fiscal position are left untouched so
        manually chosen fiscal positions are never overwritten.
        """
        partners = self.filtered(
            lambda p: p.l10n_do_dgii_tax_payer_type == "special"
            and not p.property_account_position_id
        )
        if not partners:
            return

        fiscal_position = self._l10n_do_get_special_fiscal_position()
        if fiscal_position:
            partners.property_account_position_id = fiscal_position

    @api.model_create_multi
    def create(self, vals_list):
        partners = super(Partner, self).create(vals_list)
        partners.browse(
            [
                partner.id
                for partner, vals in zip(partners, vals_list)
                if "property_account_position_id" not in vals
            ]
        )._l10n_do_set_special_fiscal_position()

        return partners

    def write(self, vals):
        res = super(Partner, self).write(vals)
        self._check_l10n_do_fiscal_fields(vals)
        if "property_account_position_id" not in vals:
            self._l10n_do_set_special_fiscal_position()

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

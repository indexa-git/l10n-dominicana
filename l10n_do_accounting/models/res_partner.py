from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError

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

    @api.model
    def _l10n_do_sanitize_vat(self, vat: str, country_id: int | bool = False) -> str:
        """Strip every non digit character from a Dominican RNC or Cedula.

        Args:
            vat: VAT number as typed by the user.
            country_id: id of the country the VAT belongs to. VAT numbers of
                any other country are returned untouched.

        Returns:
            str: digits only VAT for Dominican contacts, unchanged value
                otherwise. Leading/trailing spaces, dots and dashes are
                dropped along with any other non digit character.
        """
        if country_id != self.env.ref("base.do").id:
            return vat

        return "".join(char for char in vat if char.isdigit())

    @api.onchange("vat", "country_id")
    def _onchange_l10n_do_vat(self):
        """Clean up the VAT on the form so the user sees the stored value."""
        if self.vat:
            self.vat = self._l10n_do_sanitize_vat(self.vat, self.country_id.id)

    @api.constrains("vat", "country_id")
    def _check_l10n_do_vat(self):
        """Dominican VAT must be a 9 digit RNC or an 11 digit Cedula."""
        for partner in self:
            if partner.country_code != "DO" or not partner.vat:
                continue

            if not partner.vat.isdigit() or len(partner.vat) not in (9, 11):
                raise ValidationError(
                    _(
                        "%(vat)s is not a valid RNC/Cédula for %(partner)s. "
                        "It must contain digits only: 9 for a RNC or 11 for "
                        "a Cédula.",
                        vat=partner.vat,
                        partner=partner.display_name,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        default_country_id = None
        for vals in vals_list:
            if not vals.get("vat"):
                continue

            if "country_id" in vals:
                country_id = vals["country_id"]
            else:
                # Dominican companies default this field, so it must be
                # resolved to know whether the VAT has to be sanitized.
                if default_country_id is None:
                    default_country_id = self.default_get(["country_id"]).get(
                        "country_id", False
                    )
                country_id = default_country_id

            vals["vat"] = self._l10n_do_sanitize_vat(vals["vat"], country_id)

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
        countries = self.mapped("country_id")
        if vals.get("vat") and len(countries) == 1:
            country_id = vals["country_id"] if "country_id" in vals else countries.id
            vals = dict(vals, vat=self._l10n_do_sanitize_vat(vals["vat"], country_id))

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

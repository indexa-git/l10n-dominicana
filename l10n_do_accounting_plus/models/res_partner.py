from odoo import models, fields, api, _
from odoo.exceptions import AccessError
from zeep import Client

class Partner(models.Model):
    _inherit = "res.partner"

    def _get_l10n_do_dgii_payer_types_selection(self):
        """Return the list of payer types needed in invoices to clasify accordingly to
        DGII requirements."""
        return [
            ("taxpayer", _("Fiscal Tax Payer")),
            ("non_payer", _("Non Tax Payer")),
            ("minor", _("Minor expenses")),
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
                    ("company_id.partner_id.country_id.code", "=", "DO"),
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
        """ Compute the type of partner depending on soft decisions"""
        company_id = self.env["res.company"].search(
            [("id", "=", self.env.user.company_id.id)]
        )
        for partner in self:
            vat = str(partner.vat if partner.vat else partner.name)
            is_dominican_partner = bool(partner.country_id == self.env.ref("base.do"))

            if partner.country_id and not is_dominican_partner:
                partner.l10n_do_dgii_tax_payer_type = "foreigner"

            elif vat and (
                not partner.l10n_do_dgii_tax_payer_type
                or partner.l10n_do_dgii_tax_payer_type == "non_payer"
            ):
                if partner.country_id and is_dominican_partner:
                    if vat.isdigit() and len(vat) == 9:
                        if not partner.vat:
                            partner.vat = vat
                        if partner.name and "MINISTERIO" in partner.name:
                            partner.l10n_do_dgii_tax_payer_type = "governmental"
                        elif partner.name and any(
                            [n for n in ("IGLESIA", "ZONA FRANCA") if n in partner.name]
                        ):
                            partner.l10n_do_dgii_tax_payer_type = "special"
                        elif vat.startswith("1"):
                            partner.l10n_do_dgii_tax_payer_type = "taxpayer"
                        elif vat.startswith("4"):
                            partner.l10n_do_dgii_tax_payer_type = "nonprofit"
                        else:
                            partner.l10n_do_dgii_tax_payer_type = "taxpayer"

                    elif len(vat) == 11:
                        if vat.isdigit():
                            if not partner.vat:
                                partner.vat = vat
                            payer_type = (
                                "taxpayer"
                                if company_id.l10n_do_default_client == "fiscal"
                                else "non_payer"
                            )
                            partner.l10n_do_dgii_tax_payer_type = payer_type
                        else:
                            partner.l10n_do_dgii_tax_payer_type = "non_payer"
                    else:
                        partner.l10n_do_dgii_tax_payer_type = "non_payer"
            elif not partner.l10n_do_dgii_tax_payer_type:
                partner.l10n_do_dgii_tax_payer_type = "non_payer"
            else:
                partner.l10n_do_dgii_tax_payer_type = (
                    partner.l10n_do_dgii_tax_payer_type
                )

    def _inverse_l10n_do_dgii_tax_payer_type(self):
        for partner in self:
            partner.l10n_do_dgii_tax_payer_type = partner.l10n_do_dgii_tax_payer_type

    @api.model
    def validate_rnc_cedula(self, fiscal_id):
        invalid_fiscal_id_message = (500, u"RNC/Cédula invalido", u"El número de RNC/Cedula no es valido.")
        try:
            res = Client(wsdl='https://dgii.gov.do/wsMovilDGII/WSMovilDGII.asmx?WSDL')
            dgii_data = eval(res.service.GetContribuyentes(fiscal_id,0,0,1,''))
            if dgii_data:
                #dgii_data = res.json()
                dgii_data["vat"] = dgii_data['RGE_RUC']
                dgii_data["name"] = dgii_data['RGE_NOMBRE']
                dgii_data["comment"] = u"Nombre Comercial: {}, regimen de pago: {},  estatus: {}, categoria: {}".format(
                                    dgii_data['NOMBRE_COMERCIAL'], 
                                    dgii_data.get('REGIMEN_PAGOS', ""), 
                                    dgii_data['ESTATUS'],
                                    dgii_data['CATEGORIA'])
                if len(fiscal_id) == 9:
                    dgii_data.update({"company_type": u"company"})
                    dgii_data.update({"is_company": u"True"})
                else:
                    dgii_data.update({"company_type": u"person"})

                return 1, dgii_data
            else:
                return 0, invalid_fiscal_id_message
        except:
            return 0, 'Error conexion DGII'

    @api.onchange("name","vat")
    def onchange_partner_name(self):
        valido = 0
        if self.vat and len(self.vat) in (9,11):
            valido, dgii_data = self.validate_rnc_cedula(self.vat)
        elif self.name and len(self.name) in (9,11):
            valido, dgii_data = self.validate_rnc_cedula(self.name)
        if valido == 1:
            self.vat = dgii_data['vat']
            self.name = dgii_data['name']
            self.comment = dgii_data['comment']
            self.company_type = dgii_data['company_type']
        # self.message_post(body='Prueba', subject='Prueba')
        # else:
        #     for rec in self:
        #         rec.message_post(body="prueba")
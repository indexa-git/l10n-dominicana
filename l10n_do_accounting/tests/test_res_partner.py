from . import common
from odoo.tests import tagged


@tagged("-at_install", "post_install")
class ResPartnerTest(common.L10nDOTestsCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref="do"):
        super(ResPartnerTest, cls).setUpClass(chart_template_ref=chart_template_ref)

        cls.special_fiscal_position = cls.env[
            "res.partner"
        ]._l10n_do_get_special_fiscal_position()

    def test_001_special_partner_gets_fiscal_position_on_create(self):
        """Exempt (special) partners get the Special Regimes fiscal position"""

        self.assertTrue(self.special_fiscal_position)

        partner = self.env["res.partner"].create(
            {
                "name": "ZONA FRANCA SANTIAGO SRL",
                "vat": "130862154",
                "country_id": self.env.ref("base.do").id,
            }
        )

        self.assertEqual(partner.l10n_do_dgii_tax_payer_type, "special")
        self.assertEqual(
            partner.property_account_position_id, self.special_fiscal_position
        )

    def test_002_non_special_partner_keeps_no_fiscal_position(self):
        """Partners of any other payer type are left untouched"""

        partner = self.env["res.partner"].create(
            {
                "name": "MERCADO DEL VALLE SRL",
                "vat": "131793916",
                "country_id": self.env.ref("base.do").id,
            }
        )

        self.assertEqual(partner.l10n_do_dgii_tax_payer_type, "taxpayer")
        self.assertFalse(partner.property_account_position_id)

    def test_003_special_partner_gets_fiscal_position_on_write(self):
        """Existing exempt partners get the fiscal position when saved again"""

        partner = self.env["res.partner"].create(
            {
                "name": "MERCADO DEL VALLE SRL",
                "vat": "131793916",
                "country_id": self.env.ref("base.do").id,
            }
        )
        self.assertFalse(partner.property_account_position_id)

        partner.write({"name": "ZONA FRANCA DEL VALLE SRL"})

        self.assertEqual(partner.l10n_do_dgii_tax_payer_type, "special")
        self.assertEqual(
            partner.property_account_position_id, self.special_fiscal_position
        )

    def test_004_manual_fiscal_position_is_not_overwritten(self):
        """A manually set fiscal position is never replaced"""

        fiscal_position = self.env["account.fiscal.position"].create(
            {
                "name": "Dummy Fiscal Position",
                "company_id": self.env.company.id,
            }
        )
        partner = self.env["res.partner"].create(
            {
                "name": "ZONA FRANCA LAS AMERICAS SRL",
                "vat": "101168481",
                "country_id": self.env.ref("base.do").id,
                "property_account_position_id": fiscal_position.id,
            }
        )
        self.assertEqual(partner.property_account_position_id, fiscal_position)

        partner.write({"phone": "8090000000"})

        self.assertEqual(partner.property_account_position_id, fiscal_position)

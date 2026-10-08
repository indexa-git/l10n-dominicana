from . import common
from odoo.tests import tagged
from odoo.exceptions import ValidationError


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

    def test_005_dominican_vat_is_sanitized_on_create(self):
        """Dominican VAT is stored with digits only"""

        partner = self.env["res.partner"].create(
            {
                "name": "INDEXA SRL",
                "vat": " 131-79391-6 ",
                "country_id": self.env.ref("base.do").id,
            }
        )

        self.assertEqual(partner.vat, "131793916")

    def test_006_dominican_vat_is_sanitized_on_write(self):
        """An already saved contact also gets its VAT cleaned up"""

        partner = self.env["res.partner"].create(
            {
                "name": "JOSE LUIS LOPEZ",
                "vat": "131793916",
                "country_id": self.env.ref("base.do").id,
            }
        )

        partner.write({"vat": "224-0055969-0"})

        self.assertEqual(partner.vat, "22400559690")

    def test_007_foreign_vat_is_not_sanitized(self):
        """Contacts from any other country keep their VAT untouched"""

        partner = self.env["res.partner"].create(
            {
                "name": "FOREIGN COMPANY",
                "vat": "12.345-X",
                "country_id": self.env.ref("base.ht").id,
            }
        )

        self.assertEqual(partner.vat, "12.345-X")

    def test_008_dominican_vat_length_is_enforced(self):
        """Only 9 digit RNC and 11 digit Cédula are accepted"""

        with self.assertRaises(ValidationError):
            self.env["res.partner"].with_context(no_vat_validation=True).create(
                {
                    "name": "WRONG VAT SRL",
                    "vat": "1234567",
                    "country_id": self.env.ref("base.do").id,
                }
            )

    def test_009_rnc_and_cedula_lengths_are_accepted(self):
        """Both DGII identification lengths pass the check"""

        do_country_id = self.env.ref("base.do").id
        rnc_partner = self.env["res.partner"].create(
            {
                "name": "ITERATIVO SRL",
                "vat": "101168481",
                "country_id": do_country_id,
            }
        )
        cedula_partner = self.env["res.partner"].create(
            {
                "name": "JOSE LUIS LOPEZ",
                "vat": "22400559690",
                "country_id": do_country_id,
            }
        )

        self.assertEqual(len(rnc_partner.vat), 9)
        self.assertEqual(len(cedula_partner.vat), 11)

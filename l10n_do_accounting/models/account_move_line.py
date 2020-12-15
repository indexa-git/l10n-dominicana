from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    l10n_do_itbis_amount = fields.Monetary(
        string="ITBIS Amount",
        store=True,
        readonly=True,
        currency_field="currency_id",
    )

    def _get_price_total_and_subtotal(
        self,
        price_unit=None,
        quantity=None,
        discount=None,
        currency=None,
        product=None,
        partner=None,
        taxes=None,
        move_type=None,
    ):
        self.ensure_one()
        res = super(AccountMoveLine, self)._get_price_total_and_subtotal(
            price_unit=price_unit,
            quantity=quantity,
            discount=discount,
            currency=currency,
            product=product,
            partner=partner,
            taxes=taxes,
            move_type=move_type,
        )

        if self.move_id.is_ecf_invoice:

            line_itbis_taxes = self.tax_ids.filtered(
                lambda t: t.tax_group_id == self.env.ref("l10n_do.group_itbis")
            )
            itbis_taxes_data = line_itbis_taxes.compute_all(
                price_unit=self.price_unit,
                quantity=self.quantity,
            )
            res["l10n_do_itbis_amount"] = sum(
                [t["amount"] for t in itbis_taxes_data["taxes"]]
            )
        return res

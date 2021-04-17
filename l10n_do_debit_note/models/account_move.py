from odoo import models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_debit_line_tax(self, debit_date):

        if self.type == "out_invoice":
            return (
                self.company_id.account_sale_tax_id
                or self.env.ref("l10n_do.1_tax_18_sale")
                if (debit_date - self.invoice_date).days <= 30
                and self.partner_id.l10n_do_dgii_tax_payer_type != "special"
                else self.env.ref("l10n_do.1_tax_0_sale") or False
            )
        else:
            return self.company_id.account_purchase_tax_id or self.env.ref(
                "l10n_do.1_tax_0_purch"
            )

    def _move_autocomplete_invoice_lines_create(self, vals_list):

        ctx = self.env.context
        debit_type = ctx.get("l10n_do_debit_type")
        if debit_type and debit_type in ("percentage", "fixed_amount"):
            for vals in vals_list:
                del vals["line_ids"]
                origin_invoice_id = self.browse(self.env.context.get("active_ids"))
                price_unit = (
                    ctx.get("amount")
                    if debit_type == "fixed_amount"
                    else origin_invoice_id.amount_untaxed
                    * (ctx.get("percentage") / 100)
                )
                vals["invoice_line_ids"] = [
                    (
                        0,
                        0,
                        {
                            "name": ctx.get("reason") or _("Debit"),
                            "price_unit": price_unit,
                            "quantity": 1,
                            "tax_ids": [
                                (
                                    6,
                                    0,
                                    [
                                        origin_invoice_id._get_debit_line_tax(
                                            vals["invoice_date"]
                                        ).id
                                    ],
                                )
                            ],
                        },
                    )
                ]

        return super(AccountMove, self)._move_autocomplete_invoice_lines_create(
            vals_list
        )

    def init(self):  # DO NOT FORWARD PORT
        """
        Fill debit_origin_id field of all existing debit notes
        """

        debit_notes = self.search(
            [("is_debit_note", "=", True), ("debit_origin_id", "=", False)]
        )

        for dn in debit_notes:
            debit_origin_id = self.search(
                [("ref", "=", dn.l10n_do_origin_ncf)], limit=1
            )
            dn.debit_origin_id = debit_origin_id

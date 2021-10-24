from odoo import fields, models, api, _
from odoo.exceptions import RedirectWarning, ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _get_l10n_do_payment_form(self):
        """ Return the list of payment forms allowed by DGII. """
        return [
            ("cash", _("Cash")),
            ("bank", _("Check / Transfer")),
            ("card", _("Credit Card")),
            ("credit", _("Credit")),
            ("swap", _("Swap")),
            ("bond", _("Bonds or Gift Certificate")),
            ("others", _("Other Sale Type")),
        ]

    l10n_do_payment_form = fields.Selection(
        selection="_get_l10n_do_payment_form",
        string="Payment Form",
    )

    def _get_all_ncf_types(self, types_list, invoice=False):
        """
        Include ECF type prefixes if company is ECF issuer
        :param types_list: NCF list used to create fiscal sequences
        :return: types_list
        """

        ecf_types = ["e-%s" % d for d in types_list if d not in ("unique", "import")]

        if self._context.get("use_documents", False) or not invoice:
            # When called from Journals return all ncf+ecf types to
            # create fiscal sequences
            return types_list + ecf_types

        if (
            invoice.is_purchase_document()
            and invoice.partner_id.l10n_do_dgii_tax_payer_type
            and invoice.partner_id.l10n_do_dgii_tax_payer_type
            in ("non_payer", "foreigner")
        ):
            # Return ncf/ecf types depending on company ECF issuing status
            return ecf_types if self.company_id.l10n_do_ecf_issuer else types_list

        return types_list + ecf_types

    @api.model
    def _get_l10n_do_ncf_types_data(self):
        return {
            "issued": {
                "taxpayer": ["fiscal"],
                "non_payer": ["consumer", "unique"],
                "nonprofit": ["fiscal"],
                "special": ["special"],
                "governmental": ["governmental"],
                "foreigner": ["export", "consumer"],
            },
            "received": {
                "taxpayer": ["fiscal"],
                "non_payer": ["informal", "minor"],
                "nonprofit": ["special", "governmental"],
                "special": ["fiscal", "special", "governmental"],
                "governmental": ["fiscal", "special", "governmental"],
                "foreigner": ["import", "exterior"],
            },
        }

    def _get_journal_ncf_types(self, counterpart_partner=False, invoice=False):
        """
        Regarding the DGII type of company and the type of journal
        (sale/purchase), get the allowed NCF types. Optionally, receive
        the counterpart partner (customer/supplier) and get the allowed
        NCF types to work with him. This method is used to populate
        document types on journals and also to filter document types on
        specific invoices to/from customer/supplier
        """
        self.ensure_one()
        ncf_types_data = self._get_l10n_do_ncf_types_data()

        if not self.company_id.vat:
            action = self.env.ref("base.action_res_company_form")
            msg = _("Cannot create chart of account until you configure your VAT.")
            raise RedirectWarning(msg, action.id, _("Go to Companies"))

        # Get all the ncf_types values from the nested dictionary, remove duplicates and
        # convert it into a list
        ncf_types = list(
            set(
                [
                    value
                    for dic in ncf_types_data[
                        "issued" if self.type == "sale" else "received"
                    ].values()
                    for value in dic
                ]
            )
        )
        # TODO: check if the following commented code is still necessary
        #  considering journals don't create fiscal sequence in v14
        # if not counterpart_partner:
        #     ncf_notes = ["debit_note", "credit_note"]
        #     ncf_external = ["fiscal", "special", "governmental"]
        #
        #     # When Journal fiscal sequence create, include ncf_notes if sale
        #     # or exclude ncf_external if purchase
        #     res = (
        #         ncf_types + ncf_notes
        #         if self.type == "sale"
        #         else [ncf for ncf in ncf_types if ncf not in ncf_external]
        #     )
        #     return self._get_all_ncf_types(res)
        if counterpart_partner.l10n_do_dgii_tax_payer_type:
            counterpart_ncf_types = ncf_types_data[
                "issued" if self.type == "sale" else "received"
            ][counterpart_partner.l10n_do_dgii_tax_payer_type]
            ncf_types = list(set(ncf_types) & set(counterpart_ncf_types))
        else:
            raise ValidationError(
                _("Partner %s is needed to issue a fiscal invoice")
                % self._fields["l10n_do_dgii_tax_payer_type"].string
            )
        if invoice and invoice.move_type in ["out_refund", "in_refund"]:
            ncf_types = ["credit_note"]

        if (
            invoice
            and invoice.debit_origin_id
            or self.env.context.get("internal_type") == "debit_note"
        ):
            return ["debit_note", "e-debit_note"]

        return self._get_all_ncf_types(ncf_types, invoice)

    def _get_journal_codes(self):
        self.ensure_one()
        if self.type == "purchase":
            return []
        return ["E"] if self.company_id.l10n_do_ecf_issuer else ["B"]

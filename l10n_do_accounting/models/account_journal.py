from odoo import fields, models, api, _
from odoo.exceptions import RedirectWarning, ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _get_l10n_do_payment_form(self):
        """Return the list of payment forms allowed by DGII."""
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
    l10n_do_document_type_ids = fields.One2many(
        "l10n_do.account.journal.document_type",
        "journal_id",
        string="Document types",
        copy=False,
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

        if invoice.is_purchase_document() and any(
            t in types_list for t in ("minor", "informal", "exterior")
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
        if not counterpart_partner:
            ncf_notes = ["debit_note", "credit_note"]
            ncf_external = ["fiscal", "special", "governmental"]

            # When Journal document type create, include ncf_notes if sale
            # or exclude ncf_external if purchase
            res = (
                ncf_types + ncf_notes
                if self.type == "sale"
                else [ncf for ncf in ncf_types if ncf not in ncf_external]
            )
            return self._get_all_ncf_types(res)
        if counterpart_partner.l10n_do_dgii_tax_payer_type:
            if counterpart_partner == self.company_id.partner_id:
                ncf_types = ["minor"]
            else:
                counterpart_ncf_types = ncf_types_data[
                    "issued" if self.type == "sale" else "received"
                ][counterpart_partner.l10n_do_dgii_tax_payer_type]
                ncf_types = list(set(ncf_types) & set(counterpart_ncf_types))
        else:
            raise ValidationError(
                _("Partner (%s) %s is needed to issue a fiscal invoice")
                % (
                    counterpart_partner.id,
                    counterpart_partner._fields["l10n_do_dgii_tax_payer_type"].string,
                )
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
        elif self.type == "sale" and self.company_id.l10n_do_ecf_issuer:
            return ["E"]
        return ["B"]

    def _l10n_do_create_document_types(self):
        self.ensure_one()

        if (
            not self.l10n_latam_use_documents
            or self.company_id.country_id != self.env.ref("base.do")
        ):
            return

        document_types = self.l10n_do_document_type_ids
        fiscal_types = self._get_journal_ncf_types()

        if self.type == "purchase":
            fiscal_types = [
                ftype
                for ftype in fiscal_types
                if ftype not in ("fiscal", "credit_note")
            ]

        domain = [
            ("country_id.code", "=", "DO"),
            ("l10n_do_ncf_type", "in", fiscal_types),
        ]
        documents = self.env["l10n_latam.document.type"].search(domain)
        for document in documents.filtered(
            lambda doc: doc.l10n_do_ncf_type
            not in document_types.l10n_latam_document_type_id.mapped("l10n_do_ncf_type")
        ):
            document_types |= (
                self.env["l10n_do.account.journal.document_type"]
                .sudo()
                .create(
                    {
                        "journal_id": self.id,
                        "l10n_latam_document_type_id": document.id,
                    }
                )
            )

    @api.model_create_multi
    def create(self, vals_list):
        journals = super(AccountJournal, self).create(vals_list)

        for journal in journals:
            journal._l10n_do_create_document_types()

        return journals

    def write(self, values):
        to_check = {"type", "l10n_latam_use_documents"}
        res = super(AccountJournal, self).write(values)
        if to_check.intersection(set(values.keys())):
            for rec in self:
                rec._l10n_do_create_document_types()
        return res


class AccountJournalDocumentType(models.Model):
    _name = "l10n_do.account.journal.document_type"
    _description = "Journal Document Type"

    journal_id = fields.Many2one(
        "account.journal", "Journal", required=True, readonly=True
    )
    l10n_latam_document_type_id = fields.Many2one(
        "l10n_latam.document.type", "Document type", required=True, readonly=True
    )
    l10n_do_ncf_expiration_date = fields.Date(
        string="Expiration date",
        required=True,
        default=fields.Date.end_of(
            fields.Date.today().replace(month=12, year=fields.Date.today().year + 1),
            "year",
        ),
    )
    company_id = fields.Many2one(
        string="Company", related="journal_id.company_id", readonly=True
    )

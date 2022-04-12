from re import compile

from odoo import models, fields, _
from odoo.exceptions import ValidationError


class L10nLatamDocumentType(models.Model):
    _inherit = "l10n_latam.document.type"

    def _get_l10n_do_ncf_types(self):
        """Return a list of fiscal types and their respective sequence type to be used
        on sequences, journals and document types."""
        return [
            ("fiscal", "01"),
            ("consumer", "02"),
            ("debit_note", "03"),
            ("credit_note", "04"),
            ("informal", "11"),
            ("unique", "12"),
            ("minor", "13"),
            ("special", "14"),
            ("governmental", "15"),
            ("export", "16"),
            ("exterior", "17"),
            ("e-fiscal", "31"),
            ("e-consumer", "32"),
            ("e-debit_note", "33"),
            ("e-credit_note", "34"),
            ("e-informal", "41"),
            ("e-minor", "43"),
            ("e-special", "44"),
            ("e-governmental", "45"),
            ("e-export", "46"),
            ("e-exterior", "47"),
            ("in_fiscal", "01"),
        ]

    l10n_do_ncf_type = fields.Selection(
        selection="_get_l10n_do_ncf_types",
        string="NCF types",
        help="NCF types defined by the DGII that can be used to identify the"
        " documents presented to the government and that depends on the"
        " operation type, the responsibility of both the issuer and the"
        " receptor of the document",
    )
    l10n_do_ncf_expiration_date = fields.Date(  # Deprecated. Do not forward port.
        string="NCF Expiration date",
        required=True,
        default=fields.Date.end_of(fields.Date.today(), "year"),
    )
    internal_type = fields.Selection(
        selection_add=[
            ("in_invoice", "Supplier Invoices"),
            ("in_credit_note", "Supplier Credit Note"),
            ("in_debit_note", "Supplier Debit Note"),
        ],
        ondelete={
            "in_invoice": "cascade",
            "in_credit_note": "cascade",
            "in_debit_note": "cascade",
        },
    )
    is_vat_required = fields.Boolean(
        default=False,
    )

    def _format_document_number(self, document_number):
        """Make validation of Import Dispatch Number
        * making validations on the document_number.
        * format the document_number against a pattern and return it
        """
        self.ensure_one()
        if self.country_id != self.env.ref("base.do"):
            return super()._format_document_number(document_number)

        if not document_number:
            return False

        # NCF/ECF validation regex
        regex = r"^(P?((?=.{13})E)type(\d{10})|(((?=.{11})B))type(\d{8}))$".replace(
            "type", dict(self._get_l10n_do_ncf_types())[self.l10n_do_ncf_type]
        )
        pattern = compile(regex)

        if not bool(pattern.match(document_number)):
            raise ValidationError(
                _("NCF %s doesn't have the correct structure") % document_number
            )

        return document_number

from . import models

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    cr.execute(
        "UPDATE account_invoice SET is_ecf_invoice = is_ecf;"
    )
    cr.execute(
        "UPDATE account_invoice SET l10n_do_ncf_expiration_date = ncf_expiration_date;"
    )
    cr.execute(
        """UPDATE account_invoice ai
            SET l10n_do_ecf_security_code = ed.e_security_code
            FROM ecf_document ed
            WHERE ai.ecf_document = ed.id
            AND ai.l10n_do_ecf_security_code IS NULL
            AND ed.e_security_code IS NOT NULL;"""
    )
    cr.execute(
        """UPDATE account_invoice ai
            SET l10n_do_ecf_sign_date = ed.signature_date
            FROM ecf_document ed
            WHERE ai.ecf_document = ed.id
            AND ai.l10n_do_ecf_sign_date IS NULL
            AND ed.signature_date IS NOT NULL;"""
    )
    cr.execute(
        """UPDATE account_invoice ai
            SET l10n_do_electronic_stamp = ed.ecf_stamp
            FROM ecf_document ed
            WHERE ai.ecf_document = ed.id
            AND ai.l10n_do_electronic_stamp IS NULL
            AND ed.ecf_stamp IS NOT NULL;"""
    )

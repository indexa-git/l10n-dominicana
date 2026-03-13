from . import models

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    cr.execute(
        "UPDATE account_invoice SET l10n_do_fiscal_number = dgii_document_number;"
    )
    cr.execute(
        "UPDATE account_invoice SET l10n_do_origin_ncf = origin_out;"
    )
    cr.execute(
        "UPDATE account_journal SET l10n_latam_use_documents = use_documents;"
    )
    cr.execute(
        "UPDATE account_journal SET l10n_do_payment_form = payment_form;"
    )
    cr.execute(
        "UPDATE account_invoice SET l10n_do_expense_type = expense_type;"
    )
    cr.execute(
        "UPDATE account_invoice SET l10n_do_cancellation_type = anulation_type;"
    )
    cr.execute(
        "UPDATE account_invoice SET l10n_do_income_type = income_type;"
    )
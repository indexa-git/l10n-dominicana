

# Account Invoice Tests

# TODO: all invoice types (out_invoice, in_invoice, out_refund, in_refund,
#  out_debit, in_debit) fiscal_sequence_id is computed correctly

# TODO: an invoice does not get a fiscal sequence if invoice date >= fiscal
#  sequence expiration date

# TODO: invoice fiscal_sequence_status is computed correctly

# TODO: on change journal_id, if not fiscal, invoice fiscal_type_id and
#  fiscal_sequence_id = False

# TODO: when _onchange_fiscal_type(), if fiscal_type_id.journal_id then
#  invoice journal_id = fiscal_type_id.journal_id

# TODO: when _onchange_partner_id, if out_invoice and not fiscal_type_id,
#  invoice fiscal_type_id = partner_id.fiscal_type_id

# TODO: when _onchange_partner_id, if in_invoice,
#  fiscal_type_id = partner_id.fiscal_type_id
#  and expense_type = partner_id.expense_type

# TODO: when out_invoice validate, if not partner_id.sale_fiscal_type_id,
#  partner_id.sale_fiscal_type_id =  invoice.fiscal_type_id

# TODO: when in_invoice validate, if not partner_id.purchase_fiscal_type_id,
#  partner_id.purchase_fiscal_type_id = invoice.fiscal_type_id and if not
#  partner_id.expense_type, partner_id.expense_type = invoice.expense_type

# TODO: when invoice validate, if fiscal_type_id.required_document and
#  not partner_id.vat, raise UserError

# TODO: when out_invoice, out_refund validate,
#  if fiscal_type_id != unico ingreso and amount_total >= 250,000
#  raise UserError

# TODO: a random number of random types invoices always get the
#  right NCF when validate

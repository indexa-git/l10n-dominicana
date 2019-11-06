

# Account Fiscal Sequence Tests

# TODO: only one fiscal sequence per type can be in queue
# TODO: warning_gap is correctly computed
# TODO: sequence_remaining is correctly computed
# TODO: next_fiscal_number is correctly computed
# TODO: default sequence_start is correctly computed
# TODO: unique active sequence ValidationError raised
# TODO: _validate_sequence_range() ValidationErrors raised
# TODO: internal sequence is deleted when fiscal sequence is deleted
# TODO: fiscal sequence is auto expired if expiration_date is today
# TODO: when a draft fiscal sequence is confirmed, a internal sequence is created too with correct vals
# TODO: when a draft fiscal sequence is confirmed, a new internal sequence is attached and state == 'active'
# TODO: when a fiscal sequence is cancelled, its internal sequence is set to inactive and state == 'cancelled'
# TODO: a fiscal sequence is auto-depleted when its get out of available sequences
# TODO: a fiscal sequence of random type always returns the correct combination of prefix-padding-sequence string

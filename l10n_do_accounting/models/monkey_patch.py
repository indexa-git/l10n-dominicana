from collections import defaultdict
from odoo import models, api
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends("posted_before", "state", "journal_id", "date")
    def _compute_name(self):
        def journal_key(move):
            return (move.journal_id, move.journal_id.refund_sequence and move.move_type)

        def date_key(move):
            return (move.date.year, move.date.month)

        grouped = defaultdict(  # key: journal_id, move_type
            lambda: defaultdict(  # key: first adjacent (date.year, date.month)
                lambda: {
                    "records": self.env["account.move"],
                    "format": False,
                    "format_values": False,
                    "reset": False,
                }
            )
        )
        self = self.sorted(lambda m: (m.date, m.ref or "", m.id))
        highest_name = self[0]._get_last_sequence(lock=False) if self else False

        # Group the moves by journal and month
        for move in self:
            if (
                not highest_name
                and move == self[0]
                and not move.posted_before
                and move.date
            ):
                # In the form view, we need to compute a default sequence so that the user can edit
                # it. We only check the first move as an approximation (enough for new in form view)
                pass
            elif (move.name and move.name != "/") or move.state != "posted":
                try:
                    if not move.posted_before:
                        move._constrains_date_sequence()
                    # Has already a name or is not posted, we don't add to a batch
                    continue
                except ValidationError:
                    # Has never been posted and the name doesn't match the date: recompute it
                    pass
            group = grouped[journal_key(move)][date_key(move)]
            if not group["records"]:
                # Compute all the values needed to sequence this whole group
                move._set_next_sequence()
                (
                    group["format"],
                    group["format_values"],
                ) = move._get_sequence_format_param(move.name)
                group["reset"] = move._deduce_sequence_number_reset(move.name)
            group["records"] += move

        # Fusion the groups depending on the sequence reset and the format used because `seq` is
        # the same counter for multiple groups that might be spread in multiple months.
        final_batches = []
        for journal_group in grouped.values():
            journal_group_changed = True
            for date_group in journal_group.values():
                if (
                    journal_group_changed
                    or final_batches[-1]["format"] != date_group["format"]
                    or dict(final_batches[-1]["format_values"], seq=0)
                    != dict(date_group["format_values"], seq=0)
                ):
                    final_batches += [date_group]
                    journal_group_changed = False
                elif date_group["reset"] == "never":
                    final_batches[-1]["records"] += date_group["records"]
                elif (
                    date_group["reset"] == "year"
                    and final_batches[-1]["records"][0].date.year
                    == date_group["records"][0].date.year
                ):
                    final_batches[-1]["records"] += date_group["records"]
                else:
                    final_batches += [date_group]

        # Give the name based on previously computed values
        for batch in final_batches:
            for move in batch["records"]:
                move.name = batch["format"].format(**batch["format_values"])
                batch["format_values"]["seq"] += 1
            batch["records"]._compute_split_sequence()

        self.filtered(lambda m: not m.name).name = "/"

        for move in self.filtered(
            lambda x: x.country_code == "DO"
            and x.l10n_latam_document_type_id
            and not x.l10n_latam_manual_document_number
            and not x.l10n_do_enable_first_sequence
        ):
            move.with_context(is_l10n_do_seq=True)._set_next_sequence()

# -*- coding: utf-8 -*-

from openerp import models, fields, api
import number_to_word


class account_payment(models.Model):
    _inherit = "account.payment"

    def get_amont_in_word(self):
        self.amont_in_word = number_to_word.to_word(self.amount, self.currency_id.name)

    amont_in_word = fields.Char("En letras", compute=get_amont_in_word)


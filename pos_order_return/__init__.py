##########################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd.
#    (<https://webkul.com/>)
###########################################################################
from . import models


def pre_init_check(cr):
    from odoo.service import common
    from odoo import _
    from odoo.exceptions import UserError
    version_info = common.exp_version()
    server_serie = version_info.get('server_serie')
    if server_serie != '11.0':
        raise UserError(_(
            'Module support Odoo series 11.0 found {}.'.format(server_serie)))
    return True

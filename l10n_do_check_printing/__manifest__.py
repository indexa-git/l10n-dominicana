# -*- coding: utf-8 -*-
###############################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL.
#  (<https://marcos.do/>)

#  Write by Eneldo Serrata (eneldo@marcos.do)
#  See LICENSE file for full copyright and licensing details.
#
# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used
# (nobody can redistribute (or sell) your module once they have bought it,
# unless you gave them your consent)
# if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without
# copying any source code or material from the Software. You may distribute
# those modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the
# Softwar or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
# USE OR OTHER DEALINGS IN THE SOFTWARE.
###############################################################################

{
    'name': 'Impresion de cheques bancos Domnicanos',
    'version': '1.0',
    'author': 'Eneldo Serrata - Marcos Organizador de Negocios, SRL.',
    'website': "http://marcos.do",
    'category': 'Localization',

    'summary': """
    Localizacion Para Republica Dominicana
    Permite configurar desde los diarios las plantillas para impresion de
    chques.""",
    'description': """
        Este módulo permite configurar sus cheques de pagos en el papel de
        verificación pre-impreso.
        Puede configurar la salida (distribución, información trozos, etc.)
        en los entornos de la empresa, y gestionar el cheques de numeración
        (si utiliza cheques preimpresos sin números) en la configuración de
        diario.
    """,
    'depends': ['account_check_printing', 'ncf_manager', 'account_cancel'],
    'data': [
        'security/ir.model.access.csv',
        'report/paper_data.xml',
        'report/report_data.xml',
        'report/report_template.xml',
        'views/account_view.xml',
        'views/account_cancel_view.xml',
        'views/check_report_config_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': "Other proprietary"
}

# -*- coding: utf-8 -*-
########################################################################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL. (<https://marcos.do/>)
#  Write by Eneldo Serrata (eneldo@marcos.do)
#  See LICENSE file for full copyright and licensing details.
#
# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used
# (nobody can redistribute (or sell) your module once they have bought it, unless you gave them your consent)
# if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
########################################################################################################################

from odoo import models, api
from zeep import Client
import json


class DgiiWs(models.Model):
    _name = "dgii.ws"

    dgii_ws = u"http://www.dgii.gov.do/wsMovilDGII/WSMovilDGII.asmx?WSDL"

    @api.model
    def GetContribuyentes(self, value, patronBusqueda=0, inicioFilas=0, filaFilas=100, IMEI="public"):
        client = Client(self.dgii_ws)
        res = client.service.GetContribuyentes(value[0], patronBusqueda=patronBusqueda, inicioFilas=inicioFilas, filaFilas=filaFilas, IMEI=IMEI)
        return json.loads(res)

    def GetContribuyentesCount(self, value, IMEI="public"):
        res = self.client.GetContribuyentesCount(value, IMEI=IMEI)
        return json.loads(res)

    def GetDocumento(self, codigoBusqueda, patronBusqueda=0, IMEI="public"):
        res = self.service.client(codigoBusqueda, patronBusqueda=patronBusqueda, IMEI=IMEI)
        return json.loads(res)

    def GetNCF(self, RNC, NCF, IMEI="public"):
        res = self.service.client.GetNCF(RNC, NCF, IMEI=IMEI)
        return json.loads(res)

    def GetPlaca(self, RNC, Placa, IMEI="public"):
        res = self.service.client.GetPlaca(RNC, Placa, IMEI=IMEI)
        return json.loads(res)

    def GetVehiculoPorDATAMATRIX(self, value, IMEI="public"):
        res =  self.service.client.GetVehiculoPorDATAMATRIX(value, IMEI=IMEI)
        return json.loads(res)



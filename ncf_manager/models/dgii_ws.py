# -*- coding: utf-8 -*-
# ######################################################################
# © 2015-2018 Marcos Organizador de Negocios SRL. (https://marcos.do/)
#             Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 iterativo SRL. (https://iterativo.do/)
#             Gustavo Valverde <gustavo@iterativo.do>

# This file is part of NCF Manager.

# NCF Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# NCF Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with NCF Manager.  If not, see <http://www.gnu.org/licenses/>.
# ######################################################################

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



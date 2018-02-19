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

from odoo import models, api, exceptions
from zeep import Client
import json
from stdnum import get_cc_module
from stdnum.do import rnc
from stdnum.do import cedula
from stdnum.do import ncf
from stdnum.exceptions import InvalidFormat, InvalidChecksum, InvalidLength, InvalidComponent


# get_cc_module("do", "vat").validate("101733934")
# get_cc_module("do", "cedula").validate("00111616876")
# get_cc_module("do", "ncf").validate("A010010010100000001")

# do.cedula Cedula (Dominican Republic national identification number).

# do.ncf 	NCF (Números de Comprobante Fiscal, Dominican Republic receipt number).
# do.rnc 	RNC (Registro Nacional del Contribuyente, Dominican Republic tax number).

# The ncf and rnc modules also have a check_dgii() function that can be
# used to validate the number using the DGII online web service and
# return extra information on the number.
# rnc.check_dgii("00111616876")
# rnc.check_dgii("101733934")
# from stdnum.do import ncf
# ncf.check_dgii("101733934", "A010010010100000001")


class DgiiWs(models.TransientModel):
    _name = "dgii.ws"

    dgii_ws = u"http://www.dgii.gov.do/wsMovilDGII/WSMovilDGII.asmx?WSDL"

    @api.model
    def vat_check(self, vat):
        """
        vat only validate if its size is 9 positions for rnc or 11 positions for cedulas
        and it should be a string of only numbers
        :param vat:
        :return: dict   {'category': '0',
                         'commercial_name': 'E Y M IMPORTADORES ',
                         'name': 'E Y M IMPORTADORES SRL',
                         'payment_regime': '2',
                         'rnc': '101733934',
                         'status': '2'}

                         0 if it is not a numeric string
        """
        result = 0
        if not vat.isdigit():
            return result

        try:
            if len(vat) == 9:
                get_cc_module("do", "vat").validate(vat)
            else:
                get_cc_module("do", "cedula").validate(vat)
        except InvalidFormat:
            raise exceptions.ValidationError("El número tiene un formato inválido.")
        except InvalidChecksum:
            raise exceptions.ValidationError(
                "La suma de comprobación numérica y el dígito de verificación no son válidos.")
        except InvalidLength:
            raise exceptions.ValidationError("El número tiene una longitud inválida")
        except InvalidComponent:
            raise exceptions.ValidationError("Una de las partes del número es inválida o desconocida.")
        except:
            raise exceptions.ValidationError("Vuelva a intentarlo")

        dgii_result = rnc.check_dgii(vat)
        if dgii_result:
            if dgii_result.get("status", False) == '1':
                raise exceptions.ValidationError("Esta empresa no se encuentra activa en la DGII")

            result = dgii_result

        return result

    @api.model
    def GetContribuyentes(self, value, patronBusqueda=0, inicioFilas=0, filaFilas=100, IMEI="public"):
        client = Client(self.dgii_ws)
        res = client.service.GetContribuyentes(value[0], patronBusqueda=patronBusqueda, inicioFilas=inicioFilas,
                                               filaFilas=filaFilas, IMEI=IMEI)
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
        res = self.service.client.GetVehiculoPorDATAMATRIX(value, IMEI=IMEI)
        return json.loads(res)

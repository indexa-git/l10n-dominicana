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
from odoo import models, api, exceptions, _
from zeep import Client
import json
from stdnum.do import rnc, cedula


RNC_MESSAGE = u"El RNC introducido no es válido"
CEDULA_MESSAGE = u"La cédula introducida no es válida"

excepcionesCedulas = ['00208430205', '00101118022', '00167311001',
                      '00102025201', '02755972001', '01038813907',
                      '01810035037', '00161884001', '00102630192',
                      '00000021249', '00144435001', '00100350928',
                      '00100523399', '00109402756', '00101659661',
                      '00539342005', '00104662561', '08016809001',
                      '05500012039', '00104486903', '00103754365',
                      '01200014133', '10983439110', '08498619001',
                      '00104862525', '00100729795', '00644236001',
                      '01650257001', '00170009162', '00651322001',
                      '00297018001', '00100288929', '00190002567',
                      '01094560111', '01300020331', '00109785951',
                      '00110047715', '05400067703', '00100061945',
                      '00100622461', '02831146001', '10462157001',
                      '00100728113', '00108497822', '00481106001',
                      '00100181057', '10491297001', '00300244009',
                      '00170115579', '02038569001', '00100238382',
                      '03852380001', '00100322649', '00107045499',
                      '00100384523', '00130610001', '06486186001',
                      '00101621981', '00201023001', '00520207699',
                      '00300636564', '00000140874', '05700071202',
                      '03100673050', '00189405093', '00105328185',
                      '10061805811', '00117582001', '00103443802',
                      '00100756082', '00100239662', '04700027064',
                      '04700061076', '05500023407', '05500017761',
                      '05400049237', '05400057300', '05600038964',
                      '05400021759', '00100415853', '05500032681',
                      '05500024190', '06400011981', '05500024135',
                      '06400007916', '05500014375', '05500008806',
                      '05500021118', '05600051191', '00848583056',
                      '00741721056', '04801245892', '04700004024',
                      '00163709018', '05600267737', '00207327056',
                      '00731054054', '00524571001', '00574599001',
                      '00971815056', '06800008448', '04900011690',
                      '03111670001', '00134588056', '04800019561',
                      '05400040523', '05400048248', '05600038251',
                      '00222017001', '06100011935', '06100007818',
                      '00129737056', '00540077717', '00475916056',
                      '00720758056', '02300062066', '02700029905',
                      '02600094954', '11700000658', '03100109611',
                      '04400002002', '03400157849', '03900069856',
                      '00100524531', '00686904003', '00196714003',
                      '00435518003', '00189213001', '06100009131',
                      '02300085158', '02300047220', '00100593378',
                      '00100083860', '00648496171', '00481595003',
                      '00599408003', '00493593003', '00162906003',
                      '00208832003', '00166533003', '00181880003',
                      '00241997013', '00299724003', '00174729003',
                      '01000005580', '00400012957', '00100709215',
                      '08900001310', '05400053627', '05400055770',
                      '08800003986', '02300031758', '01154421047',
                      '00300013835', '00300011700', '01300001142',
                      '00147485003', '00305535206', '05400054156',
                      '06100016486', '00100172940', '04800046910',
                      '00101527366', '00270764013', '00184129003',
                      '05400033166', '05400049834', '05400062459',
                      '09700003030', '05300013029', '05400037495',
                      '05400028496', '05400059956', '05400072273',
                      '02300052220', '00356533003', '00163540003',
                      '00376023023', '00362684023', '00633126023',
                      '00278005023', '00235482001', '00142864013',
                      '00131257003', '00236245013', '00757398001',
                      '00146965001', '00516077003', '00425759001',
                      '00857630012', '06843739551', '02300023225',
                      '00298109001', '00274652001', '00300017875',
                      '00300025568', '01300005424', '00103266558',
                      '00174940001', '00289931003', '00291549003',
                      '02800021761', '02800029588', '01000268998',
                      '02600036132', '00200040516', '01100014261',
                      '02800000129', '01200033420', '02800025877',
                      '00300020806', '00200021994', '00200063601',
                      '07600000691', '09300006239', '00200028716',
                      '04900028443', '00163549012', '01200008613',
                      '01200011252', '01100620962', '00100255349',
                      '00108796883', '03102828522', '00000719400',
                      '00004110056', '00000065377', '00000292212',
                      '00000078587', '00000126295', '00000111941',
                      '12019831001', '00171404771', '03000411295',
                      '00000564933', '00000035692', '00143072001',
                      '03102936385', '00000155482', '00000236621',
                      '00400001552', '04941042001', '00300169535',
                      '00102577448', '03600127038', '00100174666',
                      '00100378440', '00104785104', '00101961125',
                      '05600063115', '00110071113', '00100000169',
                      '04902549001', '00155144906', '06337850001',
                      '02300054193', '00100016495', '00101821735',
                      '00544657001', '03807240010', '08952698001',
                      '00345425001', '06100013662', '08900005064',
                      '05400058964', '05400022042', '05400055485',
                      '05400016031', '05400034790', '05400038776',
                      '05400076481', '05400060743', '05400047674',
                      '00246160013', '00116256005', '00261011013',
                      '01600026316', '00103983004', '05600037761',
                      '00291431001', '00100530588', '01600009531',
                      '05500022399', '05500003079', '05500006796',
                      '05500027749', '06400014372', '00352861001',
                      '00100053841', '00218507031', '02300037618',
                      '04600198229', '00000058035', '04700074827',
                      '04700070460', '04700020933', '07800000968',
                      '00300019575', '00100126468', '00300001538',
                      '03100984652', '00388338093', '58005174058',
                      '00100074627', '00100531007', '00000669773',
                      '00100430989', '00000144491', '00000404655',
                      '00000031417', '00000302347', '00000195576',
                      '00000129963', '00000045342', '00000547495',
                      '00409169001', '00166457056', '00001965804',
                      '03102399233', '03100332296', '03100442457',
                      '03170483480', '03100620176', '00572030001',
                      '00300040413', '05600166034', '03100789636',
                      '03101456639', '00107075090', '00104966313',
                      '03100001162', '03103202719', '03100231390',
                      '03101713684', '03100083297', '03101977306',
                      '03100195659', '03102342076', '03100232921',
                      '03102678700', '03100486248', '01133025660',
                      '07401860112', '01103552230', '00300015531',
                      '00160405001', '05400065376', '08900004344',
                      '05400052300', '05400057684', '05700004693',
                      '03100277078', '00108940225', '03100156525',
                      '03107049671', '03101162278', '03100771674',
                      '09400022178', '03131503831', '04200012900',
                      '04700211635', '03101014877', '03100018730',
                      '03100831768', '03101105802', '03101577963',
                      '01200027863', '01200038298', '03101409196',
                      '03100304632', '09200533048', '03102805428',
                      '03100034839', '03108309308', '03101477254',
                      '00077584000', '00101234090', '00100336027',
                      '00100384268', '00100664086', '00103766231',
                      '03103317617', '03100398552', '03100668294',
                      '05400878578', '05900105969', '05300013204',
                      '00500335596', '00561269169', '08000213172',
                      '08400068380', '04700728184', '00010130085',
                      '05300123494', '00010628559', '21000000000']


excepcionesRNC = ['501378067', '501656006', '501620371', '501651319',
                  '501651845', '501651926', '501670785', '501676936',
                  '501658167', '505038691', '501680158', '501341601',
                  '501651823', '504680029', '504681442', '504654542']


def mod10(cedula, alphabet='0123456789'):
    """
    Aplica el Algoritmo de Luhn para validar la numeración de la
    Cédula de Identidad Personal

    :param cedula: recibe una numeración cédula
    """
    cedula = cedula.replace("-", "")
    num = list(map(int, cedula))
    base = len(alphabet)

    odd_sum = sum(num[::2])
    even_sum = sum([sum(divmod(2 * d, base)) for d in num[1::2]])
    return (odd_sum + even_sum) % 10 == 0


def mod11_rnc(rnc):
    """
    Aplica el Algoritmo de Modulus 11 para validar la numeración del
    Registro Nacional del Contribuyente. El peso utilizado no es el original
    del Mod 11, ya que la DGII utiliza su propio sistema de peso para validar
    la integridad del RNC.

    Primero se remueve el dígito de verificador del parámetro de rnc recibido,
    y solo se validan 8 dígitos, ya que el peso utilizado por la DGII solo
    posee 8 posiciones.

    Cada dígito del RNC se  multiplica por su peso, y los resultados se suman.
    Luego el resultado de la suma divide entre 11, para identificar el
    remanente.

    Para generar el dígito verificador (dv), se valida el remanente:
     - Si el remanente es igual a 0, el dv es 2.
     - Si el remanente es igual a 1, el dv es 1.
     - Si el remannente es otro número, debe calcularse el dv.


    :param rnc: recibe una numeración de RNC
    """
    rnc = rnc.replace("-", "")
    number = rnc[:-1]
    rnc_weight = [7, 9, 8, 6, 5, 4, 3, 2]
    result = sum(p * (int(r)) for p, r in zip(rnc_weight, number)) % 11
    check_digit = str((10 - result) % 9 + 1)

    return check_digit == rnc[-1]


def is_identification(value):
    """
    Valida las identificaciones fiscales de la República Dominicana
    Cédula de identidad personal y Registro nacional del contribuyente
    :param value: recibe una cédula o RNC
    """
    if not value:
        return False

    # Valida que solo sean números con la longitud correcta:
    if value.isdigit() and len(value) in (9, 11):
        value = value.strip()

        # Valida en el listado de excepciones antes de aplicar los algoritmos,
        # de encontrar una coicidencia, es una identificación válida.
        if value in (excepcionesCedulas, excepcionesRNC):
            return True

        # Si es de 11 caracteres y no está en el listado
        # aplica el algoritmo de LUHN:
        elif len(value) == 11:
            value = mod10(value)

        # Si es de 9 caracteres y no está en el listado
        # aplica el algoritmo de Modulus 11:
        elif len(value) == 9:
            value = mod11_rnc(value)

    return value


def is_ncf(value, type):
    """
    Valida estructura del Número de Comprobante Ficasl (NCF)
    para República Dominicana.

    Caracter 1: Serie
        Valores Permitidos: A o P
    Caracter 2-3: División de Negocios
        Valores Permitidos: 1 al 99
    Caracter 4-6: Punto de Emisión
        Valores Permitidos: 1 al 999
    Caracter 7-9: Area de Impresión
        Valores Permitidos: 1 al 999
    Caracter 10-11: Tipo de Comprobante
        Valores Permitidos: 01, 02, 03, 04, 11, 12, 13, 14, 15
    Caracter 12-19: Secuendial
        Valores Permitidos: 1 al 99,999,999 (sin comas)

    Tamaño: 19 Caracteres

    :param value: string con NCF

    :returns: True cuando tiene exito, False cuando falla.
    """
    if not value:
        return False

    if len(value) == 19 and value[0] in 'AP' and value[1:].isdigit():
        if (type in ("in_refund", "out_refund") and value[9:11] in ('03', '04')
            or type == "in_invoice" and value[9:11] in ('01', '03', '11',
                                                        '12', '13', '14', '15')
            or type == "out_invoice" and value[9:11] in ('01', '02', '03',
                                                         '12', '14', '15')):
            return True
    return False

def validate_rnc_cedula(number):
    if len(number) > 9:
        if not cedula.is_valid(number):
            raise exceptions.ValidationError(_(CEDULA_MESSAGE))

    if not rnc.is_valid(number) and len(number)  == 9:
        raise exceptions.ValidationError(_(RNC_MESSAGE))

    dgii_vals = rnc.check_dgii(number)
    if not dgii_vals:
        return {}

    return {
        'name': dgii_vals.get('name', False) or dgii_vals.get(
            'commercial_name', ""),
        'is_company': True if len(number) == 9 else False,
        'sale_fiscal_type': "fiscal" if len(number) == 9 else "final",
        'vat': dgii_vals.get('rnc'),
        'status': dgii_vals.get('status'),
    }

class DgiiWs(models.TransientModel):
    _name = "dgii.ws"

    dgii_wsdl = "http://www.dgii.gov.do/wsMovilDGII/WSMovilDGII.asmx?WSDL"

    @api.model
    def GetContribuyentes(self, value, patronBusqueda=0, inicioFilas=0, filaFilas=100, IMEI="public"):
        client = Client(self.dgii_ws)
        res = client.service.GetContribuyentes(value[0],
            patronBusqueda=patronBusqueda, inicioFilas=inicioFilas,
            filaFilas=filaFilas, IMEI=IMEI)
        return json.loads(res)

    def GetContribuyentesCount(self, value, IMEI="public"):
        res = self.client.GetContribuyentesCount(value, IMEI=IMEI)
        return json.loads(res)

    def GetDocumento(self, codigoBusqueda, patronBusqueda=0, IMEI="public"):
        res = self.service.client(
            codigoBusqueda, patronBusqueda=patronBusqueda, IMEI=IMEI)
        return json.loads(res)

    def GetPlaca(self, RNC, Placa, IMEI="public"):
        res = self.service.client.GetPlaca(RNC, Placa, IMEI=IMEI)
        return json.loads(res)

    def GetVehiculoPorDATAMATRIX(self, value, IMEI="public"):
        res = self.service.client.GetVehiculoPorDATAMATRIX(value, IMEI=IMEI)
        return json.loads(res)

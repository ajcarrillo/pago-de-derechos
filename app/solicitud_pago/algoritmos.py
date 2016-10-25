# -*- encoding: utf-8 -*-
from datetime import date
from collections import deque

EQUIVALENCIAS_ALFANUMERICAS = {
    1: ['A', 'J'],
    2: ['B', 'K', 'S'],
    3: ['C', 'L', 'T'],
    4: ['D', 'M', 'U'],
    5: ['E', 'N', 'V'],
    6: ['F', 'O', 'W'],
    7: ['G', 'P', 'X'],
    8: ['H', 'Q', 'Y'],
    9: ['I', 'R', 'Z']
}


class M97C:
    referencia_cliente = None
    monto = None
    vigencia = None
    doble_digito_verificador = None
    constante = 2

    def __init__(self, referencia_cliente, monto, vigencia=None):
        self.referencia_cliente = str(referencia_cliente).upper()
        self.monto = float(monto)
        self.vigencia = vigencia if type(vigencia) is date else date(date.today().year, 12, 31)

    def generar(self):
        if len(self.referencia_cliente) > 32:
            raise ValueError('La referencia del cliente no puede sobrepasar los 32 caracteres')
        fecha_condensada = self.condensar_vigencia()
        if len(fecha_condensada) != 4:
            raise ValueError('La fecha condensada debe ser de exactamente 4 caracteres')
        monto_condensado = self.condensar_monto()
        if len(monto_condensado) != 1:
            raise ValueError('El monto condensado debe exactamente de 1 caracter')
            # línea de captura alfanumérica para calcular el doble dígito verificador
        linea_captura_alfanumerica = '%s%s%s%s' % (self.convertir_referencia_alfanumerica(), fecha_condensada, monto_condensado, self.constante)
        doble_digito_verificador = self.condensar_linea_captura(linea_captura_alfanumerica)
        if len(doble_digito_verificador) != 2:
            raise ValueError('El doble digito verificador no es correcto')
            # línea de captura con referencia de cliente original
        linea_captura = '%s%s%s%s' % (self.referencia_cliente, fecha_condensada, monto_condensado, self.constante)
        return '%s-%s' % (linea_captura, doble_digito_verificador)

    def condensar_linea_captura(self, linea_captura):
        residuo = self.suma_producto_ponderados(linea_captura, [11, 13, 17, 19, 23]) % 97
        return '%02d' % (residuo + 1)

    def suma_producto_ponderados(self, digitos, ponderados):
        ponderados_queue = deque(ponderados)
        suma = 0  # primero se utiliza para la suma de la multiplicación con los ponderados
        for digito in digitos[::-1]:  # monto[::-1] -> monto en reversa
            digito = int(digito)
            if len(ponderados_queue) == 0:
                ponderados_queue = deque(ponderados)
            suma += (digito * ponderados_queue.popleft())
        return suma

    def condensar_monto(self):
        monto = ''.join(('%.2f' % float(self.monto)).split('.'))
        return str(self.suma_producto_ponderados(monto, [7, 3, 1]) % 10)  # residuo de la división

    def condensar_vigencia(self):
        if type(self.vigencia) is not date:
            raise ValueError('Fecha no válida para condensar')
        periodo = (self.vigencia.year - 1988) * 372
        mes = (self.vigencia.month - 1) * 31
        dia = self.vigencia.day - 1
        return str(periodo + mes + dia)

    def convertir_referencia_alfanumerica(self):
        referencia_cliente = str(self.referencia_cliente).upper()
        referencia_alfanumerica = ''
        for caracter in referencia_cliente:
            try:
                int(caracter)
            except ValueError:
                caracter = self.equivalencia_alfanumerica(caracter)
            referencia_alfanumerica += caracter
        return referencia_alfanumerica

    def equivalencia_alfanumerica(self, caracter):
        for n in range(1, 10):
            if caracter in EQUIVALENCIAS_ALFANUMERICAS[n]:
                return str(n)
        return None


class M97Q:
    referencia_cliente = None
    monto = None
    vigencia = None
    doble_digito_verificador = None

    def __init__(self, referencia_cliente, monto, vigencia=None):
        self.referencia_cliente = str(referencia_cliente).upper()
        self.monto = float(monto)
        self.vigencia = vigencia if type(vigencia) is date else date(date.today().year, 12, 31)

    def generar(self):
        if len(self.referencia_cliente) > 32:
            raise ValueError('La referencia del cliente no puede sobrepasar los 32 caracteres')
        fecha_condensada = self.condensar_vigencia()
        if len(fecha_condensada) != 4:
            raise ValueError('La fecha condensada debe ser de exactamente 4 caracteres')
        monto_condensado = self.condensar_monto()
        if len(monto_condensado) != 1:
            raise ValueError('El monto condensado debe ser exactamente de 1 caracter')
            # linea de captura alfanumérica para calcular el doble dígito verificador
        linea_captura_alfanumerica = '%s%s%s' % (self.convertir_referencia_alfanumerica(), fecha_condensada, monto_condensado)
        doble_digito_verificador = self.condensar_linea_captura(linea_captura_alfanumerica)
        if len(doble_digito_verificador) != 2:
            raise ValueError('El doble digito verificador no es correcto')
            # línea de captura con referencia del cliente original
        linea_captura = '%s%s%s' % (self.referencia_cliente, fecha_condensada, monto_condensado)
        return '%s%s' % (linea_captura, doble_digito_verificador)

    def condensar_linea_captura(self, linea_captura):
        residuo = self.suma_producto_ponderados(linea_captura, [11, 13, 17, 19, 23]) % 97
        return '%02d' % (residuo + 1)

    def suma_producto_ponderados(self, digitos, ponderados):
        ponderados_queue = deque(ponderados)
        suma = 0  # primero se utiliza la suma de la multiplicación con los ponderados
        for digito in digitos[::-1]:  # monto[::-1] -> monto en reversa
            digito = int(digito)
            if len(ponderados_queue) == 0:
                ponderados_queue = deque(ponderados)
            suma += (digito * ponderados_queue.popleft())
        return suma

    def condensar_monto(self):
        monto = ''.join(('%.2f' % float(self.monto)).split('.'))
        return str(self.suma_producto_ponderados(monto, [7, 3, 1]) % 10)  # residuo de la división

    def condensar_vigencia(self):
        if type(self.vigencia) is not date:
            raise ValueError('Fecha no válida para condensar')
        periodo = (self.vigencia.year - 2000) * 372
        mes = (self.vigencia.month - 1) * 31
        dia = (self.vigencia.day - 1)
        return str(periodo + mes + dia)

    def convertir_referencia_alfanumerica(self):
        referencia_cliente = str(self.referencia_cliente).upper()
        referencia_alfanumerica = ''
        for caracter in referencia_cliente:
            try:
                int(caracter)
            except ValueError:
                caracter = self.equivalencia_alfanumerica(caracter)
            referencia_alfanumerica += caracter
        return referencia_alfanumerica

    def equivalencia_alfanumerica(self, caracter):
        for n in range(1, 10):
            if caracter in EQUIVALENCIAS_ALFANUMERICAS[n]:
                return str(n)
        return None

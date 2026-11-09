from __future__ import annotations

import locale
import unittest
from decimal import Decimal

from utils.formato import formatear_dinero


class FormatearDineroTest(unittest.TestCase):
    def test_cero(self) -> None:
        self.assertEqual(formatear_dinero(0), "$ 0,00")
        self.assertEqual(formatear_dinero(0.0), "$ 0,00")

    def test_none_se_muestra_como_cero(self) -> None:
        self.assertEqual(formatear_dinero(None), "$ 0,00")

    def test_enteros(self) -> None:
        self.assertEqual(formatear_dinero(5), "$ 5,00")
        self.assertEqual(formatear_dinero(999), "$ 999,00")
        self.assertEqual(formatear_dinero(1000), "$ 1.000,00")
        self.assertEqual(formatear_dinero(1234567), "$ 1.234.567,00")

    def test_decimales(self) -> None:
        self.assertEqual(formatear_dinero(1000.5), "$ 1.000,50")
        self.assertEqual(formatear_dinero(0.5), "$ 0,50")
        self.assertEqual(formatear_dinero(12.34), "$ 12,34")

    def test_redondea_a_dos_decimales(self) -> None:
        self.assertEqual(formatear_dinero(1234567.891), "$ 1.234.567,89")
        self.assertEqual(formatear_dinero(0.999), "$ 1,00")
        self.assertEqual(formatear_dinero(999.999), "$ 1.000,00")

    def test_separa_cada_tres_cifras(self) -> None:
        self.assertEqual(formatear_dinero(100000), "$ 100.000,00")
        self.assertEqual(formatear_dinero(999999.99), "$ 999.999,99")
        self.assertEqual(formatear_dinero(1000000), "$ 1.000.000,00")
        self.assertEqual(formatear_dinero(1234567890.12), "$ 1.234.567.890,12")

    def test_negativos(self) -> None:
        self.assertEqual(formatear_dinero(-1), "-$ 1,00")
        self.assertEqual(formatear_dinero(-1000.5), "-$ 1.000,50")
        self.assertEqual(formatear_dinero(-1234567.891), "-$ 1.234.567,89")

    def test_un_negativo_que_redondea_a_cero_no_lleva_signo(self) -> None:
        self.assertEqual(formatear_dinero(-0.001), "$ 0,00")
        self.assertEqual(formatear_dinero(-0.0), "$ 0,00")

    def test_decimal(self) -> None:
        self.assertEqual(formatear_dinero(Decimal("1000.5")), "$ 1.000,50")
        self.assertEqual(formatear_dinero(Decimal("1234567.891")), "$ 1.234.567,89")
        self.assertEqual(formatear_dinero(Decimal("-2500")), "-$ 2.500,00")
        self.assertEqual(formatear_dinero(Decimal("0")), "$ 0,00")

    def test_decimal_redondea_el_medio_centavo_hacia_arriba(self) -> None:
        self.assertEqual(formatear_dinero(Decimal("0.005")), "$ 0,01")
        self.assertEqual(formatear_dinero(Decimal("2.675")), "$ 2,68")

    def test_decimal_muy_grande_no_usa_notacion_cientifica(self) -> None:
        self.assertEqual(formatear_dinero(Decimal("1E+9")), "$ 1.000.000.000,00")

    def test_valores_no_finitos_no_rompen(self) -> None:
        self.assertEqual(formatear_dinero(float("nan")), "$ 0,00")
        self.assertEqual(formatear_dinero(float("inf")), "$ 0,00")
        self.assertEqual(formatear_dinero(Decimal("NaN")), "$ 0,00")

    def test_no_depende_del_locale_del_sistema(self) -> None:
        original = locale.setlocale(locale.LC_ALL)
        try:
            for nombre in ("C", "en_US.UTF-8", "English_United States.1252", "es_AR.UTF-8", "Spanish_Argentina.1252"):
                try:
                    locale.setlocale(locale.LC_ALL, nombre)
                except locale.Error:
                    continue
                self.assertEqual(formatear_dinero(1234567.891), "$ 1.234.567,89", nombre)
        finally:
            locale.setlocale(locale.LC_ALL, original)


if __name__ == "__main__":
    unittest.main()

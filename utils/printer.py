import os
from typing import List, Tuple, Optional

# Optional imports for printing backends
try:
    from escpos.printer import Usb, Network
except Exception:  # noqa
    Usb = None
    Network = None

try:
    import cups
except Exception:  # noqa
    cups = None

try:
    import win32print
    import win32ui
    import win32con
except Exception:  # noqa
    win32print = None
    win32ui = None
    win32con = None

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:  # noqa
    arabic_reshaper = None
    get_display = None


class PrinterError(Exception):
    pass


def _shape_arabic(text: str) -> str:
    if not text:
        return text
    if arabic_reshaper and get_display:
        try:
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        except Exception:
            return text
    return text


class PrinterClient:
    def __init__(self, backend: str = "escpos_usb", prefer_arabic: bool = True) -> None:
        self.backend = backend
        self.prefer_arabic = prefer_arabic

    def print_receipt(self, receipt_lines_ar: List[str], receipt_lines_en: List[str]) -> str:
        if self.prefer_arabic:
            try:
                self._print_lines_arabic(receipt_lines_ar)
                return "ar"
            except Exception:
                try:
                    self._print_lines_english(receipt_lines_en)
                    return "en"
                except Exception:
                    return "en"
        else:
            try:
                self._print_lines_english(receipt_lines_en)
                return "en"
            except Exception:
                return "en"

    def _print_lines_arabic(self, lines: List[str]) -> None:
        if self.backend == "escpos_usb" or self.backend == "escpos_network":
            if Usb is None and Network is None:
                raise PrinterError("python-escpos غير متاح")
        if self.backend == "escpos_usb":
            vendor_id_env = os.environ.get("USB_VENDOR_ID", "0")
            product_id_env = os.environ.get("USB_PRODUCT_ID", "0")
            vendor_id = int(vendor_id_env, 0) if vendor_id_env.startswith("0x") else int(vendor_id_env)
            product_id = int(product_id_env, 0) if product_id_env.startswith("0x") else int(product_id_env)
            usb_printer = Usb(vendor_id, product_id, in_ep=0x81, out_ep=0x03, timeout=0)
            self._escpos_print(usb_printer, lines, arabic=True)
        elif self.backend == "escpos_network":
            host = os.environ.get("NETWORK_PRINTER_HOST", "127.0.0.1")
            port = int(os.environ.get("NETWORK_PRINTER_PORT", "9100"))
            net_printer = Network(host, port)
            self._escpos_print(net_printer, lines, arabic=True)
        elif self.backend == "cups":
            if cups is None:
                raise PrinterError("pycups غير متاح")
            printer_name = os.environ.get("CUPS_PRINTER_NAME", "POS_Printer")
            conn = cups.Connection()
            text_data = "\n".join([_shape_arabic(line) for line in lines])
            conn.printData(printer_name, text_data.encode("utf-8"), "Receipt", {})
        elif self.backend == "win32":
            if win32print is None:
                raise PrinterError("win32print غير متاح")
            printer_name = os.environ.get("WIN32_PRINTER_NAME", win32print.GetDefaultPrinter())
            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                job = win32print.StartDocPrinter(hPrinter, 1, ("Receipt", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                data = ("\n".join([_shape_arabic(l) for l in lines]) + "\n").encode("utf-8", errors="ignore")
                win32print.WritePrinter(hPrinter, data)
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
        else:
            raise PrinterError(f"Backend غير مدعوم: {self.backend}")

    def _print_lines_english(self, lines: List[str]) -> None:
        if self.backend == "escpos_usb" or self.backend == "escpos_network":
            if Usb is None and Network is None:
                raise PrinterError("python-escpos غير متاح")
        if self.backend == "escpos_usb":
            vendor_id_env = os.environ.get("USB_VENDOR_ID", "0")
            product_id_env = os.environ.get("USB_PRODUCT_ID", "0")
            vendor_id = int(vendor_id_env, 0) if vendor_id_env.startswith("0x") else int(vendor_id_env)
            product_id = int(product_id_env, 0) if product_id_env.startswith("0x") else int(product_id_env)
            usb_printer = Usb(vendor_id, product_id, in_ep=0x81, out_ep=0x03, timeout=0)
            self._escpos_print(usb_printer, lines, arabic=False)
        elif self.backend == "escpos_network":
            host = os.environ.get("NETWORK_PRINTER_HOST", "127.0.0.1")
            port = int(os.environ.get("NETWORK_PRINTER_PORT", "9100"))
            net_printer = Network(host, port)
            self._escpos_print(net_printer, lines, arabic=False)
        elif self.backend == "cups":
            if cups is None:
                raise PrinterError("pycups غير متاح")
            printer_name = os.environ.get("CUPS_PRINTER_NAME", "POS_Printer")
            conn = cups.Connection()
            text_data = "\n".join(lines)
            conn.printData(printer_name, text_data.encode("utf-8"), "Receipt", {})
        elif self.backend == "win32":
            if win32print is None:
                raise PrinterError("win32print غير متاح")
            printer_name = os.environ.get("WIN32_PRINTER_NAME", win32print.GetDefaultPrinter())
            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                job = win32print.StartDocPrinter(hPrinter, 1, ("Receipt", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                data = ("\n".join(lines) + "\n").encode("utf-8", errors="ignore")
                win32print.WritePrinter(hPrinter, data)
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
        else:
            raise PrinterError(f"Backend غير مدعوم: {self.backend}")

    def _escpos_print(self, printer, lines: List[str], arabic: bool) -> None:
        try:
            printer.set(align='center', width=1, height=1)
        except Exception:
            pass
        for line in lines:
            text = _shape_arabic(line) if arabic else line
            try:
                printer.text(text + "\n")
            except Exception:
                try:
                    printer._raw((text + "\n").encode('utf-8'))
                except Exception:
                    pass
        try:
            printer.cut()
        except Exception:
            pass


def build_receipt_lines(market_name: str, market_address: str, market_phone: str, sale_date: str, items: List[dict], total_egp: float, seller: Optional[str] = None) -> Tuple[List[str], List[str]]:
    # Arabic lines
    lines_ar: List[str] = []
    lines_ar.append("فاتورة البيع")
    lines_ar.append(market_name)
    if market_address:
        lines_ar.append(market_address)
    if market_phone:
        lines_ar.append(market_phone)
    lines_ar.append(f"التاريخ: {sale_date}")
    if seller:
        lines_ar.append(f"البائع: {seller}")
    lines_ar.append("------------------------------")
    for item in items:
        name = item["name"]
        qty = item["quantity"]
        price = item["price_egp"]
        line_total = item["line_total"]
        lines_ar.append(f"{name}")
        lines_ar.append(f"سعر: {price:.2f} EGP | كمية: {qty} | إجمالي: {line_total:.2f}")
    lines_ar.append("------------------------------")
    lines_ar.append(f"المجموع الكلي: {total_egp:.2f} EGP")
    lines_ar.append("شكراً لتسوقكم!")

    # English fallback lines
    lines_en: List[str] = []
    lines_en.append("Sales Receipt")
    lines_en.append(market_name)
    if market_address:
        lines_en.append(market_address)
    if market_phone:
        lines_en.append(market_phone)
    lines_en.append(f"Date: {sale_date}")
    if seller:
        lines_en.append(f"Seller: {seller}")
    lines_en.append("------------------------------")
    for item in items:
        name = item["name"]
        qty = item["quantity"]
        price = item["price_egp"]
        line_total = item["line_total"]
        lines_en.append(f"{name}")
        lines_en.append(f"Price: {price:.2f} EGP | Qty: {qty} | Total: {line_total:.2f}")
    lines_en.append("------------------------------")
    lines_en.append(f"Grand Total: {total_egp:.2f} EGP")
    lines_en.append("Thanks for shopping!")

    return lines_ar, lines_en
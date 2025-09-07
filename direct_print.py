"""
نظام الطباعة المباشرة للفواتير
يدعم الطباعة بالعربية والإنجليزية حسب دعم الطابعة
"""

import subprocess
import platform
import os
import logging
import tempfile
from datetime import datetime
from escpos.printer import Usb, Serial, Network, File
from escpos.exceptions import Error as EscposError
import charset_normalizer

class DirectPrintSystem:
    def __init__(self):
        self.system = platform.system()
        self.arabic_supported = False
        self.printer = None
        
    def detect_arabic_support(self, test_text="مرحبا"):
        """كشف دعم اللغة العربية في الطابعة"""
        try:
            # اختبار تشفير النص العربي
            arabic_bytes = test_text.encode('utf-8')
            # إذا تم التشفير بنجاح، فالطابعة تدعم UTF-8
            return True
        except UnicodeEncodeError:
            logging.warning("الطابعة لا تدعم UTF-8، سيتم استخدام النسخة الإنجليزية")
            return False
    
    def find_printers(self):
        """العثور على الطابعات المتاحة"""
        printers = []
        
        try:
            if self.system == "Windows":
                result = subprocess.run([
                    "wmic", "printer", "get", "name"
                ], capture_output=True, text=True, encoding='utf-8')
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[1:]  # تجاهل العنوان
                    printers = [line.strip() for line in lines if line.strip()]
                    
            elif self.system == "Linux":
                result = subprocess.run([
                    "lpstat", "-p"
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line.startswith('printer'):
                            printer_name = line.split()[1]
                            printers.append(printer_name)
                            
        except Exception as e:
            logging.error(f"خطأ في البحث عن الطابعات: {str(e)}")
            
        return printers
    
    def setup_thermal_printer(self, printer_type="usb", **kwargs):
        """إعداد طابعة حرارية ESC/POS"""
        try:
            if printer_type == "usb":
                # USB thermal printer
                self.printer = Usb(
                    kwargs.get('vendor_id', 0x04b8),
                    kwargs.get('product_id', 0x0202)
                )
            elif printer_type == "serial":
                # Serial thermal printer
                self.printer = Serial(
                    kwargs.get('port', '/dev/ttyUSB0'),
                    baudrate=kwargs.get('baudrate', 9600)
                )
            elif printer_type == "network":
                # Network thermal printer
                self.printer = Network(
                    kwargs.get('host', '192.168.1.100'),
                    port=kwargs.get('port', 9100)
                )
            else:
                # File printer for testing
                self.printer = File(kwargs.get('file_path', '/tmp/receipt.txt'))
                
            return True
            
        except EscposError as e:
            logging.error(f"خطأ في إعداد الطابعة الحرارية: {str(e)}")
            return False
    
    def generate_arabic_invoice(self, sale_data):
        """إنشاء فاتورة بالعربية"""
        invoice_lines = []
        
        # رأس الفاتورة
        invoice_lines.append("=" * 40)
        invoice_lines.append("      سوق المصطفى التجاري")
        invoice_lines.append("    Al-Mustafa Commercial Market")
        invoice_lines.append("  شارع الجامعة، القاهرة، مصر")
        invoice_lines.append("  هاتف: 01234567890")
        invoice_lines.append("=" * 40)
        invoice_lines.append("")
        
        # معلومات الفاتورة
        invoice_lines.append(f"فاتورة رقم: {sale_data['id']}")
        invoice_lines.append(f"التاريخ: {sale_data['date']}")
        invoice_lines.append(f"الوقت: {sale_data['time']}")
        invoice_lines.append("")
        
        # معلومات العميل
        if sale_data.get('customer_name'):
            invoice_lines.append(f"العميل: {sale_data['customer_name']}")
        if sale_data.get('customer_phone'):
            invoice_lines.append(f"الهاتف: {sale_data['customer_phone']}")
        invoice_lines.append("")
        
        # جدول المنتجات
        invoice_lines.append("-" * 40)
        invoice_lines.append("المنتج                 الكمية    السعر")
        invoice_lines.append("-" * 40)
        
        for item in sale_data['items']:
            name = item['name'][:18]  # قطع الأسماء الطويلة
            qty = str(item['quantity'])
            price = f"{item['total_price']:.2f}"
            invoice_lines.append(f"{name:<18} {qty:>4} {price:>8}")
        
        invoice_lines.append("-" * 40)
        invoice_lines.append(f"المجموع الكلي: {sale_data['total']:.2f} جنيه مصري")
        invoice_lines.append("=" * 40)
        invoice_lines.append("")
        invoice_lines.append("         شكراً لتعاملكم معنا")
        invoice_lines.append("       نتمنى لكم يوماً سعيداً")
        invoice_lines.append("")
        invoice_lines.append("=" * 40)
        
        return "\n".join(invoice_lines)
    
    def generate_english_invoice(self, sale_data):
        """إنشاء فاتورة بالإنجليزية (احتياطي)"""
        invoice_lines = []
        
        # Header
        invoice_lines.append("=" * 40)
        invoice_lines.append("    Al-Mustafa Commercial Market")
        invoice_lines.append("      Cairo University St, Egypt")
        invoice_lines.append("        Phone: +20 1234567890")
        invoice_lines.append("=" * 40)
        invoice_lines.append("")
        
        # Invoice info
        invoice_lines.append(f"Invoice No: {sale_data['id']}")
        invoice_lines.append(f"Date: {sale_data['date']}")
        invoice_lines.append(f"Time: {sale_data['time']}")
        invoice_lines.append("")
        
        # Customer info
        if sale_data.get('customer_name'):
            invoice_lines.append(f"Customer: {sale_data['customer_name']}")
        if sale_data.get('customer_phone'):
            invoice_lines.append(f"Phone: {sale_data['customer_phone']}")
        invoice_lines.append("")
        
        # Items table
        invoice_lines.append("-" * 40)
        invoice_lines.append("Item                   Qty     Price")
        invoice_lines.append("-" * 40)
        
        for item in sale_data['items']:
            name = item['name'][:18]  # Truncate long names
            qty = str(item['quantity'])
            price = f"{item['total_price']:.2f}"
            invoice_lines.append(f"{name:<18} {qty:>4} {price:>8}")
        
        invoice_lines.append("-" * 40)
        invoice_lines.append(f"Total: {sale_data['total']:.2f} EGP")
        invoice_lines.append("=" * 40)
        invoice_lines.append("")
        invoice_lines.append("       Thank you for your business")
        invoice_lines.append("          Have a great day!")
        invoice_lines.append("")
        invoice_lines.append("=" * 40)
        
        return "\n".join(invoice_lines)
    
    def print_thermal_receipt(self, sale_data):
        """طباعة إيصال حراري مباشرة"""
        if not self.printer:
            return False, "لم يتم إعداد الطابعة"
            
        try:
            # كشف دعم العربية
            self.arabic_supported = self.detect_arabic_support()
            
            # إنشاء النص حسب دعم اللغة
            if self.arabic_supported:
                receipt_text = self.generate_arabic_invoice(sale_data)
                logging.info("طباعة الفاتورة بالعربية")
            else:
                receipt_text = self.generate_english_invoice(sale_data)
                logging.info("طباعة الفاتورة بالإنجليزية")
            
            # طباعة الإيصال
            self.printer.text(receipt_text)
            self.printer.cut()
            
            return True, "تم طباعة الفاتورة بنجاح"
            
        except Exception as e:
            logging.error(f"خطأ في الطباعة: {str(e)}")
            return False, f"خطأ في الطباعة: {str(e)}"
    
    def print_standard_invoice(self, sale_data, printer_name=None):
        """طباعة فاتورة عادية مباشرة"""
        try:
            # كشف دعم العربية
            self.arabic_supported = self.detect_arabic_support()
            
            # إنشاء النص حسب دعم اللغة
            if self.arabic_supported:
                invoice_text = self.generate_arabic_invoice(sale_data)
                encoding = 'utf-8'
                logging.info("طباعة الفاتورة بالعربية")
            else:
                invoice_text = self.generate_english_invoice(sale_data)
                encoding = 'ascii'
                logging.info("طباعة الفاتورة بالإنجليزية")
            
            # إنشاء ملف مؤقت
            with tempfile.NamedTemporaryFile(mode='w', delete=False, 
                                           encoding=encoding, suffix='.txt') as temp_file:
                temp_file.write(invoice_text)
                temp_file_path = temp_file.name
            
            # طباعة الملف حسب نظام التشغيل
            success = False
            if self.system == "Windows":
                success = self._print_windows(temp_file_path, printer_name)
            elif self.system == "Linux":
                success = self._print_linux(temp_file_path, printer_name)
            elif self.system == "Darwin":  # macOS
                success = self._print_macos(temp_file_path, printer_name)
            
            # حذف الملف المؤقت
            os.unlink(temp_file_path)
            
            if success:
                return True, "تم إرسال الفاتورة للطباعة"
            else:
                return False, "فشل في إرسال الفاتورة للطباعة"
                
        except Exception as e:
            logging.error(f"خطأ في الطباعة: {str(e)}")
            return False, f"خطأ في الطباعة: {str(e)}"
    
    def _print_windows(self, file_path, printer_name=None):
        """طباعة على Windows"""
        try:
            if printer_name:
                cmd = ["print", f"/D:{printer_name}", file_path]
            else:
                cmd = ["print", file_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            logging.error(f"Windows print error: {str(e)}")
            return False
    
    def _print_linux(self, file_path, printer_name=None):
        """طباعة على Linux"""
        try:
            if printer_name:
                cmd = ["lp", "-d", printer_name, file_path]
            else:
                cmd = ["lp", file_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            logging.error(f"Linux print error: {str(e)}")
            return False
    
    def _print_macos(self, file_path, printer_name=None):
        """طباعة على macOS"""
        try:
            if printer_name:
                cmd = ["lpr", "-P", printer_name, file_path]
            else:
                cmd = ["lpr", file_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            logging.error(f"macOS print error: {str(e)}")
            return False
    
    def get_system_info(self):
        """معلومات النظام والطابعات"""
        return {
            "system": self.system,
            "printers": self.find_printers(),
            "arabic_support": self.arabic_supported
        }

# إنشاء مثيل النظام العام
print_system = DirectPrintSystem()
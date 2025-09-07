import subprocess
import os
import platform
import logging
from datetime import datetime

def print_invoice_direct(invoice_path, printer_name=None):
    """Print invoice directly to printer"""
    try:
        if not os.path.exists(invoice_path):
            return False, "الملف غير موجود"
        
        system = platform.system()
        
        if system == "Windows":
            # Windows printing
            if printer_name:
                result = subprocess.run([
                    "powershell", "-Command", 
                    f"Start-Process -FilePath '{invoice_path}' -Verb Print -ArgumentList '{printer_name}'"
                ], capture_output=True, text=True)
            else:
                # Default printer
                result = subprocess.run([
                    "powershell", "-Command", 
                    f"Start-Process -FilePath '{invoice_path}' -Verb Print"
                ], capture_output=True, text=True)
                
        elif system == "Linux":
            # Linux printing using lp command
            if printer_name:
                result = subprocess.run([
                    "lp", "-d", printer_name, invoice_path
                ], capture_output=True, text=True)
            else:
                # Default printer
                result = subprocess.run([
                    "lp", invoice_path
                ], capture_output=True, text=True)
                
        elif system == "Darwin":  # macOS
            # macOS printing
            if printer_name:
                result = subprocess.run([
                    "lpr", "-P", printer_name, invoice_path
                ], capture_output=True, text=True)
            else:
                # Default printer
                result = subprocess.run([
                    "lpr", invoice_path
                ], capture_output=True, text=True)
        else:
            return False, "نظام التشغيل غير مدعوم للطباعة المباشرة"
        
        if result.returncode == 0:
            logging.info(f"Invoice {invoice_path} printed successfully")
            return True, "تم إرسال الملف للطباعة بنجاح"
        else:
            logging.error(f"Print failed: {result.stderr}")
            return False, f"خطأ في الطباعة: {result.stderr}"
            
    except Exception as e:
        logging.error(f"Print error: {str(e)}")
        return False, f"خطأ في الطباعة: {str(e)}"

def get_available_printers():
    """Get list of available printers"""
    try:
        system = platform.system()
        
        if system == "Windows":
            result = subprocess.run([
                "powershell", "-Command", 
                "Get-Printer | Select-Object Name"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[2:]  # Skip header
                printers = [line.strip() for line in lines if line.strip()]
                return printers
                
        elif system == "Linux":
            result = subprocess.run([
                "lpstat", "-p"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                printers = []
                for line in result.stdout.split('\n'):
                    if line.startswith('printer'):
                        printer_name = line.split()[1]
                        printers.append(printer_name)
                return printers
                
        elif system == "Darwin":  # macOS
            result = subprocess.run([
                "lpstat", "-p"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                printers = []
                for line in result.stdout.split('\n'):
                    if line.startswith('printer'):
                        printer_name = line.split()[1]
                        printers.append(printer_name)
                return printers
        
        return []
        
    except Exception as e:
        logging.error(f"Error getting printers: {str(e)}")
        return []

def print_receipt_thermal(sale_data, printer_name=None):
    """Print thermal receipt for POS systems"""
    try:
        # Create simple thermal receipt format
        receipt_text = generate_thermal_receipt_text(sale_data)
        
        # Save as temporary text file
        temp_file = f"static/temp/receipt_{sale_data['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        os.makedirs(os.path.dirname(temp_file), exist_ok=True)
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(receipt_text)
        
        # Print using system command
        system = platform.system()
        
        if system == "Linux":
            if printer_name:
                result = subprocess.run([
                    "lp", "-d", printer_name, "-o", "cpi=12", "-o", "lpi=8", temp_file
                ], capture_output=True, text=True)
            else:
                result = subprocess.run([
                    "lp", "-o", "cpi=12", "-o", "lpi=8", temp_file
                ], capture_output=True, text=True)
        else:
            # Fallback to regular printing
            return print_invoice_direct(temp_file, printer_name)
        
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        if result.returncode == 0:
            return True, "تم طباعة الإيصال الحراري بنجاح"
        else:
            return False, f"خطأ في طباعة الإيصال: {result.stderr}"
            
    except Exception as e:
        logging.error(f"Thermal print error: {str(e)}")
        return False, f"خطأ في الطباعة الحرارية: {str(e)}"

def generate_thermal_receipt_text(sale_data):
    """Generate thermal receipt text format"""
    receipt = []
    
    # Header
    receipt.append("=" * 40)
    receipt.append("      سوق المصطفى التجاري")
    receipt.append("    Al-Mustafa Commercial Market")
    receipt.append("=" * 40)
    receipt.append("")
    
    # Sale info
    receipt.append(f"فاتورة رقم: {sale_data['id']}")
    receipt.append(f"التاريخ: {sale_data['date']}")
    receipt.append(f"الوقت: {sale_data['time']}")
    receipt.append("")
    
    # Customer info
    if sale_data.get('customer_name'):
        receipt.append(f"العميل: {sale_data['customer_name']}")
    if sale_data.get('customer_phone'):
        receipt.append(f"الهاتف: {sale_data['customer_phone']}")
    receipt.append("")
    
    # Items
    receipt.append("-" * 40)
    receipt.append("المنتج              الكمية    السعر")
    receipt.append("-" * 40)
    
    for item in sale_data['items']:
        name = item['name'][:15]  # Truncate long names
        qty = str(item['quantity'])
        price = f"{item['total_price']:.2f}"
        receipt.append(f"{name:<15} {qty:>5} {price:>8}")
    
    receipt.append("-" * 40)
    receipt.append(f"المجموع:                   {sale_data['total']:.2f} جنيه")
    receipt.append("=" * 40)
    receipt.append("")
    receipt.append("        شكراً لتعاملكم معنا")
    receipt.append("      Thank you for your business")
    receipt.append("")
    receipt.append("=" * 40)
    
    return "\n".join(receipt)

def setup_print_queue():
    """Setup print queue and check printer connectivity"""
    try:
        printers = get_available_printers()
        if not printers:
            return False, "لا توجد طابعات متاحة"
        
        # Test print connectivity
        for printer in printers:
            try:
                system = platform.system()
                if system == "Linux":
                    result = subprocess.run([
                        "lpstat", "-p", printer
                    ], capture_output=True, text=True)
                    
                    if "enabled" in result.stdout:
                        return True, f"الطابعة {printer} جاهزة"
                        
            except Exception:
                continue
        
        return True, f"تم العثور على {len(printers)} طابعة"
        
    except Exception as e:
        logging.error(f"Print setup error: {str(e)}")
        return False, f"خطأ في إعداد الطباعة: {str(e)}"
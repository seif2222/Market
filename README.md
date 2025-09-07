# نظام إدارة السوق (Market Management System)

تطبيق Flask باللغة العربية لإدارة المنتجات والمبيعات مع دعم قارئ QR وطباعة مباشرة على طابعات POS (ESC/POS أو CUPS أو Win32) مع دعم العربية/الإنجليزية.

## المتطلبات
- Python 3.10+
- يعمل أوفلاين (SQLite محلي)
- Linux أو Windows

## التثبيت والتشغيل (Linux)
```bash
sudo apt update
sudo apt install -y python3 python3-pip libcups2-dev cups
pip install --break-system-packages -r requirements.txt || pip install --break-system-packages $(grep -v '^pycups' requirements.txt | tr '\n' ' ')
cp .env.example .env
python app.py
# افتح: http://localhost:5000
```

## التثبيت والتشغيل (Windows)
1. ثبّت Python 3.10+.
2. في PowerShell داخل مجلد المشروع:
```powershell
pip install -r requirements.txt
copy .env.example .env
# للطباعة عبر Windows API:
setx PRINTER_BACKEND win32
# اسم الطابعة (اختياري):
setx WIN32_PRINTER_NAME "Your Windows Printer Name"
python app.py
```

ملاحظة: على Windows قد لا يعمل CUPS، استخدم `PRINTER_BACKEND=win32` أو طابعات ESC/POS على الشبكة (`escpos_network`).

## الإعدادات (.env)
- MARKET_NAME, MARKET_ADDRESS, MARKET_PHONE
- PRINTER_BACKEND: escpos_usb | escpos_network | cups | win32
- PRINTER_ARABIC=1 (العربية أولاً)
- USB_VENDOR_ID, USB_PRODUCT_ID (لـ escpos_usb)
- NETWORK_PRINTER_HOST, NETWORK_PRINTER_PORT (لـ escpos_network)
- CUPS_PRINTER_NAME (لـ cups)
- WIN32_PRINTER_NAME (لـ win32)
- FLASK_DEBUG=0, FLASK_USE_RELOADER=0 (لبيئات مُدارة)

## الميزات
- استيراد المنتجات من Excel (openpyxl)
- إنشاء QR لكل منتج تلقائياً (`static/qr`)
- صفحة بيع مع دعم قارئ QR (Keyboard Emulator) وإدخال يدوي
- حفظ كل عملية بيع في SQLite مع: التاريخ والوقت، المجموع، لغة الطباعة، واسم البائع
- طباعة مباشرة على طابعات حرارية ESC/POS (USB/شبكة) أو عبر CUPS/Win32
- واجهة عربية RTL وFallback للإنجليزية إذا لم تدعم الطابعة العربية
- تقارير يومية/شهرية مع الإجمالي

## اسم البائع
- في صفحة البيع يوجد حقل "اسم البائع"، يتم تسجيله في قاعدة البيانات وطباعته في الفاتورة.

## استكشاف الأخطاء
- يتم تسجيل الأخطاء في `logs/app.log`.
- إذا فشلت العربية في الطباعة، يتم التحويل التلقائي للإنجليزية.
- تأكد من متغيرات الطابعة حسب نوعها.
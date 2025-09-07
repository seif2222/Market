# نظام إدارة السوق (Market Management System)

تطبيق Flask باللغة العربية لإدارة المنتجات والمبيعات مع دعم قارئ QR وطباعة مباشرة على طابعات POS (ESC/POS أو CUPS) مع دعم العربية/الإنجليزية.

## المتطلبات
- Python 3.10+
- نظام Linux (موصى به) أو Windows (مع تعديل الطابعة)
- قاعدة بيانات SQLite (ضمنيًا)

## التثبيت والتشغيل
1. تثبيت الحزم:
```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt || pip install $(grep -v '^pycups' requirements.txt | tr '\n' ' ')
```
2. تشغيل التطبيق:
```bash
python app.py
```
3. افتح المتصفح على: `http://localhost:5000`

## استيراد المنتجات من Excel
- يجب أن يحتوي ملف Excel على الأعمدة التالية:
  - Product ID
  - Product Name
  - Price (EGP)
  - Quantity
  - Date Added
- من صفحة "المنتجات" اختر الملف واضغط "استيراد". يتم إنشاء QR لكل منتج تلقائياً ويتم حفظ الصورة داخل `static/qr/`.

## صفحة البيع
- يمكنك إضافة المنتج يدويًا بكتابة كود المنتج أو عبر قارئ QR.
- قارئ QR يعمل كلوحة مفاتيح، يدخل الكود في حقل مخفي ويتم إضافة المنتج تلقائياً.
- عند اكتمال البيع اضغط "إتمام البيع" ليتم الحفظ في قاعدة البيانات والطباعة.

## الطباعة المباشرة
يدعم النظام 3 أنماط:
- ESC/POS عبر USB: `PRINTER_BACKEND=escpos_usb`
- ESC/POS عبر الشبكة: `PRINTER_BACKEND=escpos_network`
- CUPS (Linux): `PRINTER_BACKEND=cups`

ملف الإعدادات عبر المتغيرات (يمكن وضعها في `.env`):
- MARKET_NAME، MARKET_ADDRESS، MARKET_PHONE
- PRINTER_BACKEND (القيم: escpos_usb, escpos_network, cups)
- PRINTER_ARABIC=1 للطباعة بالعربية أولاً، 0 للإنجليزية أولاً
- إذا كان ESC/POS USB:
  - USB_VENDOR_ID (مثال: 0x04b8)
  - USB_PRODUCT_ID (مثال: 0x0e15)
- إذا كان ESC/POS شبكة:
  - NETWORK_PRINTER_HOST (مثال: 192.168.1.50)
  - NETWORK_PRINTER_PORT (افتراضي 9100)
- إذا كان CUPS:
  - CUPS_PRINTER_NAME (اسم الطابعة في النظام)

في حال عدم دعم العربية:
- يحاول النظام أولاً الطباعة بالعربية (مع تشكيل النص)، وإذا فشل يتم الطباعة الإنجليزية كبديل.

## التقارير
- صفحة "التقارير" تعرض تقارير المبيعات يومياً أو شهرياً مع الإجمالي.

## ملاحظات
- قد يتطلب `pycups` تثبيت حزم نظام: `libcups2-dev`.
- يمكن إزالة `pycups` من `requirements.txt` إذا لم تكن بحاجة إلى CUPS.
- تم استخدام Bootstrap RTL للواجهات واتجاه النص RTL.
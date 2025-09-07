from flask import render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from app import app, db
from models import User, Product, Sale, SaleItem
from direct_print import print_system
import os
from datetime import datetime
import json
import qrcode
from io import BytesIO
import base64

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('تم تسجيل الدخول بنجاح', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # إحصائيات اليوم
    today = datetime.now().date()
    today_sales = Sale.query.filter(
        Sale.sale_date >= datetime.combine(today, datetime.min.time())
    ).all()
    
    total_sales_today = len(today_sales)
    total_revenue_today = sum(sale.total_amount for sale in today_sales)
    total_products = Product.query.count()
    low_stock_products = Product.query.filter(Product.quantity <= 5).count()
    
    # آخر 5 مبيعات
    recent_sales = Sale.query.order_by(Sale.sale_date.desc()).limit(5).all()
    
    return render_template('dashboard.html',
                         total_sales_today=total_sales_today,
                         total_revenue_today=total_revenue_today,
                         total_products=total_products,
                         low_stock_products=low_stock_products,
                         recent_sales=recent_sales)

@app.route('/products')
def products():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    products = Product.query.all()
    return render_template('products.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        price = float(request.form.get('price'))
        quantity = int(request.form.get('quantity'))
        category = request.form.get('category')
        
        # إنشاء Product ID فريد
        product_id = f"P{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        product = Product(
            product_id=product_id,
            name=name,
            price=price,
            quantity=quantity,
            category=category,
            date_added=datetime.utcnow()
        )
        
        db.session.add(product)
        db.session.commit()
        
        # إنشاء QR Code
        qr_path = generate_qr_code(product)
        product.qr_code_path = qr_path
        db.session.commit()
        
        flash('تم إضافة المنتج بنجاح', 'success')
        return redirect(url_for('products'))
    
    return render_template('add_product.html')

@app.route('/sales')
def sales():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return redirect(url_for('qr_sales'))  # توجه إلى صفحة المبيعات بـ QR

@app.route('/qr_sales')
def qr_sales():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    products = Product.query.filter(Product.quantity > 0).all()
    return render_template('qr_sales.html', products=products)

@app.route('/get_product_by_qr/<product_id>')
def get_product_by_qr(product_id):
    if 'user_id' not in session:
        return jsonify({'error': 'غير مصرح'}), 401
    
    product = Product.query.filter_by(product_id=product_id).first()
    if product:
        return jsonify({
            'id': product.id,
            'product_id': product.product_id,
            'name': product.name,
            'price': product.price,
            'quantity': product.quantity,
            'category': product.category
        })
    
    return jsonify({'error': 'المنتج غير موجود'}), 404

@app.route('/process_sale', methods=['POST'])
def process_sale():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    customer_name = request.form.get('customer_name', '')
    customer_phone = request.form.get('customer_phone', '')
    cart_items = request.form.get('cart_items')
    
    if not cart_items:
        flash('لا توجد منتجات في سلة التسوق', 'error')
        return redirect(url_for('qr_sales'))
    
    cart_data = json.loads(cart_items)
    total_amount = 0
    
    # إنشاء بيانات البيع
    sale = Sale(
        customer_name=customer_name,
        customer_phone=customer_phone,
        total_amount=0  # سيتم تحديثه
    )
    
    db.session.add(sale)
    db.session.flush()  # للحصول على ID
    
    # إضافة عناصر البيع
    sale_items_data = []
    for item in cart_data:
        product = Product.query.get(item['product_id'])
        if product and product.quantity >= item['quantity']:
            # تقليل الكمية
            product.quantity -= item['quantity']
            
            # إنشاء عنصر البيع
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                quantity=item['quantity'],
                unit_price=product.price,
                total_price=product.price * item['quantity']
            )
            
            total_amount += sale_item.total_price
            db.session.add(sale_item)
            
            # حفظ بيانات العنصر للطباعة
            sale_items_data.append({
                'name': product.name,
                'quantity': item['quantity'],
                'unit_price': product.price,
                'total_price': sale_item.total_price
            })
    
    # تحديث إجمالي البيع
    sale.total_amount = total_amount
    db.session.commit()
    
    # تحضير بيانات الفاتورة للطباعة
    sale_data = {
        'id': sale.id,
        'date': sale.sale_date.strftime('%Y-%m-%d'),
        'time': sale.sale_date.strftime('%H:%M:%S'),
        'customer_name': customer_name,
        'customer_phone': customer_phone,
        'total': total_amount,
        'items': sale_items_data
    }
    
    # طباعة الفاتورة مباشرة
    try:
        # محاولة الطباعة الحرارية أولاً
        if hasattr(print_system, 'printer') and print_system.printer:
            success, message = print_system.print_thermal_receipt(sale_data)
        else:
            # طباعة عادية
            success, message = print_system.print_standard_invoice(sale_data)
        
        if success:
            # تحديث تاريخ الطباعة
            sale.print_date = datetime.utcnow()
            db.session.commit()
            flash(f'تم إتمام البيع وطباعة الفاتورة: {message}', 'success')
        else:
            flash(f'تم إتمام البيع ولكن فشلت الطباعة: {message}', 'warning')
            
    except Exception as e:
        flash(f'تم إتمام البيع ولكن حدث خطأ في الطباعة: {str(e)}', 'warning')
    
    return redirect(url_for('qr_sales'))

@app.route('/reports')
def reports():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # تصفية حسب التاريخ
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Sale.query
    
    if start_date:
        query = query.filter(Sale.sale_date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(Sale.sale_date <= datetime.strptime(end_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
    
    sales = query.order_by(Sale.sale_date.desc()).all()
    
    # إحصائيات
    total_sales = len(sales)
    total_revenue = sum(sale.total_amount for sale in sales)
    
    return render_template('reports.html', 
                         sales=sales,
                         total_sales=total_sales,
                         total_revenue=total_revenue,
                         start_date=start_date,
                         end_date=end_date)

@app.route('/print_setup')
def print_setup():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    system_info = print_system.get_system_info()
    return render_template('print_setup.html', system_info=system_info)

@app.route('/setup_thermal_printer', methods=['POST'])
def setup_thermal_printer():
    if 'user_id' not in session:
        return jsonify({'error': 'غير مصرح'}), 401
    
    printer_type = request.form.get('printer_type', 'usb')
    
    success = print_system.setup_thermal_printer(printer_type)
    
    if success:
        return jsonify({'success': True, 'message': 'تم إعداد الطابعة الحرارية بنجاح'})
    else:
        return jsonify({'success': False, 'message': 'فشل في إعداد الطابعة الحرارية'})

@app.route('/test_print')
def test_print():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # بيانات اختبار
    test_data = {
        'id': 'TEST001',
        'date': datetime.now().strftime('%Y-%m-%d'),
        'time': datetime.now().strftime('%H:%M:%S'),
        'customer_name': 'عميل تجريبي',
        'customer_phone': '01234567890',
        'total': 150.00,
        'items': [
            {'name': 'منتج تجريبي 1', 'quantity': 2, 'unit_price': 50.0, 'total_price': 100.0},
            {'name': 'منتج تجريبي 2', 'quantity': 1, 'unit_price': 50.0, 'total_price': 50.0}
        ]
    }
    
    try:
        if hasattr(print_system, 'printer') and print_system.printer:
            success, message = print_system.print_thermal_receipt(test_data)
        else:
            success, message = print_system.print_standard_invoice(test_data)
        
        if success:
            flash(f'تم اختبار الطباعة: {message}', 'success')
        else:
            flash(f'فشل اختبار الطباعة: {message}', 'error')
            
    except Exception as e:
        flash(f'خطأ في اختبار الطباعة: {str(e)}', 'error')
    
    return redirect(url_for('print_setup'))

def generate_qr_code(product):
    """إنشاء QR Code للمنتج"""
    # بيانات QR Code
    qr_data = json.dumps({
        'product_id': product.product_id,
        'name': product.name,
        'price': product.price
    })
    
    # إنشاء QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # حفظ الصورة
    qr_dir = 'static/qr_codes'
    os.makedirs(qr_dir, exist_ok=True)
    
    qr_filename = f"qr_{product.product_id}.png"
    qr_path = os.path.join(qr_dir, qr_filename)
    
    qr_image = qr.make_image(fill_color="black", back_color="white")
    qr_image.save(qr_path)
    
    return qr_path

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.price = float(request.form.get('price'))
        product.quantity = int(request.form.get('quantity'))
        product.category = request.form.get('category')
        
        db.session.commit()
        flash('تم تحديث المنتج بنجاح', 'success')
        return redirect(url_for('products'))
    
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    product = Product.query.get_or_404(product_id)
    
    # Delete QR code file if exists
    if product.qr_code_path and os.path.exists(product.qr_code_path):
        os.remove(product.qr_code_path)
    
    db.session.delete(product)
    db.session.commit()
    
    flash(f'تم حذف المنتج "{product.name}" بنجاح', 'success')
    return redirect(url_for('products'))

@app.route('/reprint_invoice/<int:sale_id>', methods=['POST'])
def reprint_invoice(sale_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    sale = Sale.query.get_or_404(sale_id)
    
    # Prepare sale data for printing
    sale_data = {
        'id': sale.id,
        'date': sale.sale_date.strftime('%Y-%m-%d'),
        'time': sale.sale_date.strftime('%H:%M:%S'),
        'customer_name': sale.customer_name,
        'customer_phone': sale.customer_phone,
        'total': sale.total_amount,
        'items': []
    }
    
    for item in sale.items:
        sale_data['items'].append({
            'name': item.product.name,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'total_price': item.total_price
        })
    
    # Print invoice
    try:
        if hasattr(print_system, 'printer') and print_system.printer:
            success, message = print_system.print_thermal_receipt(sale_data)
        else:
            success, message = print_system.print_standard_invoice(sale_data)
        
        if success:
            # Update print date
            sale.print_date = datetime.utcnow()
            db.session.commit()
            flash(f'تم إعادة طباعة الفاتورة: {message}', 'success')
        else:
            flash(f'فشلت إعادة الطباعة: {message}', 'error')
            
    except Exception as e:
        flash(f'خطأ في إعادة الطباعة: {str(e)}', 'error')
    
    return redirect(url_for('reports'))
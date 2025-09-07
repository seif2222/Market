import pandas as pd
import os
from datetime import datetime
from models import Product, db
from utils import generate_qr_code
import logging

def import_products_from_excel(file_path):
    """Import products from Excel file"""
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Expected columns: Product ID, Product Name, Price, Quantity, Date Added
        required_columns = ['Product ID', 'Product Name', 'Price', 'Quantity', 'Date Added']
        
        # Check if all required columns exist
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"الأعمدة المفقودة: {', '.join(missing_columns)}"
        
        success_count = 0
        error_count = 0
        error_messages = []
        
        for index, row in df.iterrows():
            try:
                # Check if product already exists
                existing_product = Product.query.filter_by(product_id=str(row['Product ID'])).first()
                
                if existing_product:
                    # Update existing product
                    existing_product.name = str(row['Product Name'])
                    existing_product.price = float(row['Price'])
                    existing_product.quantity = int(row['Quantity'])
                    existing_product.date_added = pd.to_datetime(row['Date Added']).to_pydatetime()
                    existing_product.excel_source = file_path
                    existing_product.updated_at = datetime.utcnow()
                    
                    # Regenerate QR code
                    qr_path = generate_qr_code(existing_product)
                    existing_product.qr_code_path = qr_path
                    
                    success_count += 1
                else:
                    # Create new product
                    product = Product(
                        product_id=str(row['Product ID']),
                        name=str(row['Product Name']),
                        price=float(row['Price']),
                        quantity=int(row['Quantity']),
                        category='مستورد من إكسيل',  # Default category for imported products
                        date_added=pd.to_datetime(row['Date Added']).to_pydatetime(),
                        excel_source=file_path
                    )
                    
                    db.session.add(product)
                    db.session.flush()  # Get the ID
                    
                    # Generate QR code
                    qr_path = generate_qr_code(product)
                    product.qr_code_path = qr_path
                    
                    success_count += 1
                    
            except Exception as e:
                error_count += 1
                error_messages.append(f"السطر {index + 2}: {str(e)}")
                continue
        
        # Commit all changes
        db.session.commit()
        
        result_message = f"تم استيراد {success_count} منتج بنجاح"
        if error_count > 0:
            result_message += f"\n{error_count} خطأ: {'; '.join(error_messages[:5])}"
            if len(error_messages) > 5:
                result_message += "..."
        
        return True, result_message
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Excel import error: {str(e)}")
        return False, f"خطأ في قراءة ملف الإكسيل: {str(e)}"

def export_products_to_excel(file_path=None):
    """Export products to Excel file"""
    try:
        if not file_path:
            file_path = f"static/exports/products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Ensure export directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Get all products
        products = Product.query.all()
        
        # Create DataFrame
        data = []
        for product in products:
            data.append({
                'Product ID': product.product_id,
                'Product Name': product.name,
                'Price': product.price,
                'Quantity': product.quantity,
                'Category': product.category,
                'Date Added': product.date_added.strftime('%Y-%m-%d') if product.date_added else '',
                'Created At': product.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Updated At': product.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        df = pd.DataFrame(data)
        
        # Write to Excel
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='المنتجات', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['المنتجات']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        return True, file_path
        
    except Exception as e:
        logging.error(f"Excel export error: {str(e)}")
        return False, f"خطأ في تصدير الملف: {str(e)}"

def validate_excel_file(file_path):
    """Validate Excel file format"""
    try:
        df = pd.read_excel(file_path)
        required_columns = ['Product ID', 'Product Name', 'Price', 'Quantity', 'Date Added']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"الأعمدة المفقودة: {', '.join(missing_columns)}"
        
        # Check data types
        errors = []
        for index, row in df.iterrows():
            try:
                float(row['Price'])
                int(row['Quantity'])
                pd.to_datetime(row['Date Added'])
            except:
                errors.append(f"السطر {index + 2}: بيانات غير صحيحة")
                if len(errors) >= 5:
                    break
        
        if errors:
            return False, "; ".join(errors)
        
        return True, "الملف صحيح"
        
    except Exception as e:
        return False, f"خطأ في قراءة الملف: {str(e)}"
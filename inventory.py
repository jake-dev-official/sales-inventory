import pandas as pd
from datetime import datetime
import db_manager

def generate_sequential_id(key_name, start=0):
    """Generates a sequential ID (e.g., 1000, 1001, 1002...)."""
    last_num = db_manager.get_metadata(key_name, start)
    if last_num is None:
        last_num = start
    else:
        last_num = int(last_num)
    
    next_num = last_num + 1
    db_manager.set_metadata(key_name, next_num)
    
    return str(next_num)

def generate_product_id():
    return generate_sequential_id('last_product_number', 999)  # Starts at 1000

def generate_invoice_id():
    return generate_sequential_id('last_invoice_number', 999)  # Starts at 1000

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def add_product(name, date_added, supplier, quantity, total_cost):
    """Adds a new product and optionally records initial stock."""
    products = db_manager.load_data('Products')
    
    if not products.empty and name in products['name'].values:
        raise ValueError(f"Product '{name}' already exists.")

    prod_id = generate_product_id()
    timestamp = get_timestamp()
    
    new_product = {
        'product_id': prod_id,
        'name': name,
        'created_at': timestamp
    }
    db_manager.append_data('Products', new_product)
    
    # Handle Initial Stock (Purchase)
    qty = int(quantity) if quantity else 0
    if qty > 0:
        total = float(total_cost) if total_cost else 0.0
        add_purchase(
            product_id=prod_id,
            quantity=qty,
            total_cost=total,
            supplier=supplier,
            date_override=date_added
        )
        
    return new_product

def get_all_products():
    """Returns products sorted by newest first."""
    products = db_manager.load_data('Products')
    if products.empty:
        return products
    
    if 'created_at' in products.columns:
        products = products.sort_values('created_at', ascending=False)
    
    return products

def get_last_supplier(product_id):
    """Returns the last supplier used for a product."""
    purchases = db_manager.load_data('Purchases')
    if purchases.empty:
        return ""
    
    product_purchases = purchases[purchases['product_id'].astype(str) == str(product_id)]
    if product_purchases.empty:
        return ""
    
    if 'date' in product_purchases.columns:
        product_purchases = product_purchases.sort_values('date', ascending=False)
    
    last_supplier = product_purchases.iloc[0].get('supplier', '')
    return last_supplier if pd.notna(last_supplier) else ""

def get_product_stock(product_id):
    """Returns the current stock level for a product."""
    purchases = db_manager.load_data('Purchases')
    sales = db_manager.load_data('Sales')
    
    total_in = 0
    if not purchases.empty:
        product_purchases = purchases[purchases['product_id'].astype(str) == str(product_id)]
        total_in = product_purchases['quantity'].sum()
    
    total_out = 0
    if not sales.empty:
        product_sales = sales[sales['product_id'].astype(str) == str(product_id)]
        total_out = product_sales['quantity'].sum()
    
    return int(total_in - total_out)

def add_purchase(product_id, quantity, total_cost, supplier, date_override=None):
    """Records a stock-in (purchase)."""
    date_val = date_override if date_override else get_timestamp()
    qty = int(quantity)
    total = float(total_cost)
    unit_cost = total / qty if qty > 0 else 0.0
    
    new_purchase = {
        'date': date_val,
        'product_id': str(product_id),
        'supplier': supplier,
        'quantity': qty,
        'total_cost': total,
        'unit_cost': unit_cost
    }
    db_manager.append_data('Purchases', new_purchase)
    return new_purchase

def add_sale(customer_name, items, payment_amount):
    """
    Records a sale.
    items: list of dicts {'product_id': str, 'name': str, 'quantity': int, 'unit_price': float}
    """
    invoice_id = generate_invoice_id()
    timestamp = get_timestamp()
    total_sale_amount = 0
    
    for item in items:
        pid = str(item['product_id'])
        qty = int(item['quantity'])
        unit_price = float(item['unit_price'])
        line_total = unit_price * qty
        total_sale_amount += line_total
        
        sale_record = {
            'invoice_id': invoice_id,
            'date': timestamp,
            'customer_name': customer_name,
            'product_id': pid,
            'product_name': item['name'],
            'quantity': qty,
            'unit_price': unit_price,
            'line_total': line_total
        }
        db_manager.append_data('Sales', sale_record)
        
    balance = total_sale_amount - float(payment_amount)
    
    invoice_record = {
        'invoice_id': invoice_id,
        'date': timestamp,
        'customer_name': customer_name,
        'total_amount': total_sale_amount,
        'payment_received': float(payment_amount),
        'balance': balance
    }
    db_manager.append_data('Invoices', invoice_record)
    
    return invoice_id, total_sale_amount, balance

def get_debts():
    """Returns all invoices with outstanding balances."""
    invoices = db_manager.load_data('Invoices')
    
    if invoices.empty or 'balance' not in invoices.columns:
        return pd.DataFrame(columns=['invoice_id', 'customer_name', 'date', 'total', 'paid', 'balance'])
    
    debts = invoices[invoices['balance'] > 0].copy()
    debts = debts.rename(columns={
        'total_amount': 'total',
        'payment_received': 'paid'
    })
    
    return debts[['invoice_id', 'customer_name', 'date', 'total', 'paid', 'balance']]

def record_payment(invoice_id, amount):
    """Records a payment against an invoice."""
    invoices = db_manager.load_data('Invoices')
    
    if invoices.empty:
        raise ValueError("No invoices found.")
    
    # Convert to string for comparison
    invoice_id = str(invoice_id)
    invoice = invoices[invoices['invoice_id'].astype(str) == invoice_id]
    if invoice.empty:
        raise ValueError(f"Invoice {invoice_id} not found.")
    
    current_balance = float(invoice.iloc[0]['balance'])
    
    if current_balance <= 0:
        raise ValueError(f"Invoice {invoice_id} has no outstanding balance.")
    
    if float(amount) > current_balance:
        raise ValueError(f"Payment (GHC {amount}) exceeds balance (GHC {current_balance}).")
    
    payment_record = {
        'invoice_id': invoice_id,
        'date': get_timestamp(),
        'amount': float(amount)
    }
    db_manager.append_data('Payments', payment_record)
    
    # Update balance in Invoices
    new_balance = current_balance - float(amount)
    new_paid = float(invoice.iloc[0]['payment_received']) + float(amount)
    
    invoices.loc[invoices['invoice_id'].astype(str) == invoice_id, 'balance'] = new_balance
    invoices.loc[invoices['invoice_id'].astype(str) == invoice_id, 'payment_received'] = new_paid
    
    with pd.ExcelWriter(db_manager.DB_FILE, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        invoices.to_excel(writer, sheet_name='Invoices', index=False)
    
    return new_balance

def delete_product(product_id):
    """Deletes a product and logs to history."""
    products = db_manager.load_data('Products')
    
    if products.empty:
        raise ValueError("No products found.")
    
    product_match = products[products['product_id'].astype(str) == str(product_id)]
    if product_match.empty:
        raise ValueError(f"Product {product_id} not found.")
    
    product_name = product_match.iloc[0]['name']
    
    history_record = {
        'action': 'DELETE',
        'entity_type': 'Product',
        'entity_id': str(product_id),
        'entity_name': product_name,
        'timestamp': get_timestamp()
    }
    db_manager.append_data('History', history_record)
    
    products = products[products['product_id'].astype(str) != str(product_id)]
    
    with pd.ExcelWriter(db_manager.DB_FILE, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        products.to_excel(writer, sheet_name='Products', index=False)

def get_inventory_report():
    """Calculates current stock levels."""
    products = get_all_products()
    purchases = db_manager.load_data('Purchases')
    sales = db_manager.load_data('Sales')
    
    report_data = []
    
    if products.empty:
        return pd.DataFrame(columns=['product_id', 'name', 'total_purchased', 'total_sold', 'current_stock'])

    for _, product in products.iterrows():
        pid = str(product['product_id'])
        
        total_in = 0
        if not purchases.empty:
            product_purchases = purchases[purchases['product_id'].astype(str) == pid]
            total_in = product_purchases['quantity'].sum()
            
        total_out = 0
        if not sales.empty:
            product_sales = sales[sales['product_id'].astype(str) == pid]
            total_out = product_sales['quantity'].sum()
            
        current_stock = total_in - total_out
        
        report_data.append({
            'product_id': pid,
            'name': product['name'],
            'total_purchased': total_in,
            'total_sold': total_out,
            'current_stock': current_stock
        })
        
    return pd.DataFrame(report_data)

# --- Company Settings ---
def get_company_info():
    return {
        'name': db_manager.get_metadata('company_name', ''),
        'address': db_manager.get_metadata('company_address', ''),
        'phone': db_manager.get_metadata('company_phone', ''),
        'email': db_manager.get_metadata('company_email', '')
    }

def save_company_info(name, address, phone, email):
    db_manager.set_metadata('company_name', name)
    db_manager.set_metadata('company_address', address)
    db_manager.set_metadata('company_phone', phone)
    db_manager.set_metadata('company_email', email)

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import inventory
import db_manager
import invoice_pdf
import os
import subprocess

class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventory Management System")
        self.root.geometry("1200x800")
        
        db_manager.initialize_db()
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.tab_settings = ttk.Frame(self.notebook)
        self.tab_inventory = ttk.Frame(self.notebook)
        self.tab_products = ttk.Frame(self.notebook)
        self.tab_purchase = ttk.Frame(self.notebook)
        self.tab_sales = ttk.Frame(self.notebook)
        self.tab_debts = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_settings, text='⚙ Settings')
        self.notebook.add(self.tab_inventory, text='Inventory Dashboard')
        self.notebook.add(self.tab_products, text='Add Product')
        self.notebook.add(self.tab_purchase, text='Restock (Purchase)')
        self.notebook.add(self.tab_sales, text='New Sale')
        self.notebook.add(self.tab_debts, text='Debts & Payments')
        
        self.setup_settings_tab()
        self.setup_inventory_tab()
        self.setup_products_tab()
        self.setup_purchase_tab()
        self.setup_sales_tab()
        self.setup_debts_tab()
        
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        self.check_company_setup()

    def check_company_setup(self):
        company = inventory.get_company_info()
        if not company.get('name'):
            messagebox.showinfo("Welcome", "Please set up your company details in the Settings tab before making sales.")
            self.notebook.select(self.tab_settings)

    def on_tab_change(self, event):
        selected_tab = self.notebook.select()
        tab_text = self.notebook.tab(selected_tab, "text")
        if tab_text == 'Inventory Dashboard':
            self.refresh_inventory_list()
        elif tab_text == 'Restock (Purchase)':
            self.refresh_purchase_products()
        elif tab_text == 'New Sale':
            self.refresh_sales_product_list()
        elif tab_text == 'Debts & Payments':
            self.refresh_debts_list()

    # --- Settings Tab ---
    def setup_settings_tab(self):
        frame = ttk.Frame(self.tab_settings)
        frame.pack(padx=30, pady=30)
        
        ttk.Label(frame, text="Company Settings", font=('Arial', 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
        
        ttk.Label(frame, text="Company Name:").grid(row=1, column=0, sticky='w', pady=5)
        self.ent_company_name = ttk.Entry(frame, width=40)
        self.ent_company_name.grid(row=1, column=1, pady=5)
        
        ttk.Label(frame, text="Address:").grid(row=2, column=0, sticky='w', pady=5)
        self.ent_company_address = ttk.Entry(frame, width=40)
        self.ent_company_address.grid(row=2, column=1, pady=5)
        
        ttk.Label(frame, text="Phone:").grid(row=3, column=0, sticky='w', pady=5)
        self.ent_company_phone = ttk.Entry(frame, width=40)
        self.ent_company_phone.grid(row=3, column=1, pady=5)
        
        ttk.Label(frame, text="Email:").grid(row=4, column=0, sticky='w', pady=5)
        self.ent_company_email = ttk.Entry(frame, width=40)
        self.ent_company_email.grid(row=4, column=1, pady=5)
        
        btn_save = ttk.Button(frame, text="Save Settings", command=self.save_company_settings)
        btn_save.grid(row=5, column=0, columnspan=2, pady=20)
        
        self.load_company_settings()

    def load_company_settings(self):
        company = inventory.get_company_info()
        self.ent_company_name.delete(0, tk.END)
        self.ent_company_name.insert(0, company.get('name', ''))
        self.ent_company_address.delete(0, tk.END)
        self.ent_company_address.insert(0, company.get('address', ''))
        self.ent_company_phone.delete(0, tk.END)
        self.ent_company_phone.insert(0, company.get('phone', ''))
        self.ent_company_email.delete(0, tk.END)
        self.ent_company_email.insert(0, company.get('email', ''))

    def save_company_settings(self):
        name = self.ent_company_name.get()
        address = self.ent_company_address.get()
        phone = self.ent_company_phone.get()
        email = self.ent_company_email.get()
        
        if not name:
            messagebox.showerror("Error", "Company name is required.")
            return
        
        try:
            inventory.save_company_info(name, address, phone, email)
            messagebox.showinfo("Success", "Company settings saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # --- Inventory Tab (No selling price column) ---
    def setup_inventory_tab(self):
        lbl_header = ttk.Label(self.tab_inventory, text="Current Stock Levels", font=('Arial', 14, 'bold'))
        lbl_header.pack(pady=10)
        
        columns = ('S/N', 'Product ID', 'Name', 'Purchased', 'Sold', 'Stock')
        self.tree_inventory = ttk.Treeview(self.tab_inventory, columns=columns, show='headings', selectmode='extended')
        
        self.tree_inventory.heading('S/N', text='S/N')
        self.tree_inventory.column('S/N', width=50)
        self.tree_inventory.heading('Product ID', text='Product ID')
        self.tree_inventory.column('Product ID', width=80)
        self.tree_inventory.heading('Name', text='Name')
        self.tree_inventory.column('Name', width=250)
        self.tree_inventory.heading('Purchased', text='Purchased')
        self.tree_inventory.column('Purchased', width=100)
        self.tree_inventory.heading('Sold', text='Sold')
        self.tree_inventory.column('Sold', width=100)
        self.tree_inventory.heading('Stock', text='Stock')
        self.tree_inventory.column('Stock', width=100)
        
        self.tree_inventory.pack(fill='both', expand=True, padx=10, pady=10)
        
        btn_frame = ttk.Frame(self.tab_inventory)
        btn_frame.pack(pady=5)
        
        btn_refresh = ttk.Button(btn_frame, text="Refresh", command=self.refresh_inventory_list)
        btn_refresh.pack(side='left', padx=5)
        
        btn_delete = ttk.Button(btn_frame, text="Delete Selected", command=self.action_delete_product)
        btn_delete.pack(side='left', padx=5)

    def refresh_inventory_list(self):
        for item in self.tree_inventory.get_children():
            self.tree_inventory.delete(item)
            
        df = inventory.get_inventory_report()
        if not df.empty:
            for idx, (_, row) in enumerate(df.iterrows(), 1):
                self.tree_inventory.insert('', 'end', values=(
                    idx,
                    row['product_id'],
                    row['name'],
                    row['total_purchased'],
                    row['total_sold'],
                    row['current_stock']
                ))

    def action_delete_product(self):
        selected = self.tree_inventory.selection()
        if not selected:
            messagebox.showerror("Error", "Please select one or more products to delete.")
            return
        
        product_names = []
        for sel in selected:
            item = self.tree_inventory.item(sel)
            product_names.append(item['values'][2])
        
        confirm = messagebox.askyesno("Confirm Delete", 
                                      f"Delete {len(selected)} product(s)?\n\n" + "\n".join(product_names))
        if confirm:
            errors = []
            for sel in selected:
                item = self.tree_inventory.item(sel)
                product_id = item['values'][1]
                try:
                    inventory.delete_product(product_id)
                except Exception as e:
                    errors.append(f"{item['values'][2]}: {str(e)}")
            
            if errors:
                messagebox.showwarning("Partial Success", "Some products could not be deleted:\n\n" + "\n".join(errors))
            else:
                messagebox.showinfo("Success", f"{len(selected)} product(s) deleted.")
            
            self.refresh_inventory_list()

    # --- Add Product Tab (No selling price) ---
    def setup_products_tab(self):
        frame = ttk.Frame(self.tab_products)
        frame.pack(padx=20, pady=20)
        
        ttk.Label(frame, text="Product Name:").grid(row=0, column=0, sticky='w', pady=5)
        self.ent_prod_name = ttk.Entry(frame, width=30)
        self.ent_prod_name.grid(row=0, column=1, pady=5)
        
        ttk.Separator(frame, orient='horizontal').grid(row=1, column=0, columnspan=2, sticky='ew', pady=15)
        ttk.Label(frame, text="Initial Stock Details (Optional)", font=('Arial', 10, 'bold')).grid(row=2, column=0, columnspan=2, pady=5)
        
        ttk.Label(frame, text="Date (YYYY-MM-DD):").grid(row=3, column=0, sticky='w', pady=5)
        self.ent_prod_date = ttk.Entry(frame, width=30)
        self.ent_prod_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_prod_date.grid(row=3, column=1, pady=5)
        
        ttk.Label(frame, text="Supplier:").grid(row=4, column=0, sticky='w', pady=5)
        self.ent_prod_supplier = ttk.Entry(frame, width=30)
        self.ent_prod_supplier.grid(row=4, column=1, pady=5)
        
        ttk.Label(frame, text="Quantity:").grid(row=5, column=0, sticky='w', pady=5)
        self.ent_prod_qty = ttk.Entry(frame, width=30)
        self.ent_prod_qty.grid(row=5, column=1, pady=5)
        self.ent_prod_qty.bind('<KeyRelease>', self.calc_product_cost_per_item)
        
        ttk.Label(frame, text="Total Cost (GHC):").grid(row=6, column=0, sticky='w', pady=5)
        self.ent_prod_total_cost = ttk.Entry(frame, width=30)
        self.ent_prod_total_cost.grid(row=6, column=1, pady=5)
        self.ent_prod_total_cost.bind('<KeyRelease>', self.calc_product_cost_per_item)
        
        ttk.Label(frame, text="Cost Per Item:").grid(row=7, column=0, sticky='w', pady=5)
        self.lbl_prod_cost_per_item = ttk.Label(frame, text="GHC 0.00", font=('Arial', 10, 'bold'))
        self.lbl_prod_cost_per_item.grid(row=7, column=1, sticky='w', pady=5)
        
        btn_add = ttk.Button(frame, text="Add Product & Stock", command=self.action_add_product)
        btn_add.grid(row=8, column=0, columnspan=2, pady=20)

    def calc_product_cost_per_item(self, event=None):
        try:
            qty = float(self.ent_prod_qty.get())
            total_cost = float(self.ent_prod_total_cost.get())
            cost_per_item = total_cost / qty if qty > 0 else 0
            self.lbl_prod_cost_per_item.config(text=f"GHC {cost_per_item:.2f}")
        except ValueError:
            self.lbl_prod_cost_per_item.config(text="GHC 0.00")

    def action_add_product(self):
        name = self.ent_prod_name.get()
        date_added = self.ent_prod_date.get()
        supplier = self.ent_prod_supplier.get()
        qty = self.ent_prod_qty.get()
        total_cost = self.ent_prod_total_cost.get()
        
        if not name:
            messagebox.showerror("Error", "Product Name is required.")
            return
            
        try:
            inventory.add_product(name, date_added, supplier, qty, total_cost)
            messagebox.showinfo("Success", f"Product '{name}' added successfully.")
            
            self.ent_prod_name.delete(0, tk.END)
            self.ent_prod_supplier.delete(0, tk.END)
            self.ent_prod_qty.delete(0, tk.END)
            self.ent_prod_total_cost.delete(0, tk.END)
            self.lbl_prod_cost_per_item.config(text="GHC 0.00")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # --- Purchase Tab ---
    def setup_purchase_tab(self):
        frame = ttk.Frame(self.tab_purchase)
        frame.pack(padx=20, pady=20)
        
        ttk.Label(frame, text="Select Product:").grid(row=0, column=0, sticky='w', pady=5)
        self.cb_purchase_prod = ttk.Combobox(frame, state="readonly", width=30)
        self.cb_purchase_prod.grid(row=0, column=1, pady=5)
        self.cb_purchase_prod.bind('<<ComboboxSelected>>', self.on_purchase_product_selected)
        
        ttk.Label(frame, text="Date (YYYY-MM-DD):").grid(row=1, column=0, sticky='w', pady=5)
        self.ent_purchase_date = ttk.Entry(frame, width=30)
        self.ent_purchase_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_purchase_date.grid(row=1, column=1, pady=5)
        
        ttk.Label(frame, text="Supplier:").grid(row=2, column=0, sticky='w', pady=5)
        self.ent_purchase_supplier = ttk.Entry(frame, width=30)
        self.ent_purchase_supplier.grid(row=2, column=1, pady=5)
        
        self.lbl_last_supplier = ttk.Label(frame, text="", foreground='gray')
        self.lbl_last_supplier.grid(row=2, column=2, sticky='w', padx=10)
        
        ttk.Label(frame, text="Quantity:").grid(row=3, column=0, sticky='w', pady=5)
        self.ent_purchase_qty = ttk.Entry(frame, width=30)
        self.ent_purchase_qty.grid(row=3, column=1, pady=5)
        self.ent_purchase_qty.bind('<KeyRelease>', self.calc_purchase_cost_per_item)
        
        ttk.Label(frame, text="Total Cost (GHC):").grid(row=4, column=0, sticky='w', pady=5)
        self.ent_purchase_total_cost = ttk.Entry(frame, width=30)
        self.ent_purchase_total_cost.grid(row=4, column=1, pady=5)
        self.ent_purchase_total_cost.bind('<KeyRelease>', self.calc_purchase_cost_per_item)
        
        ttk.Label(frame, text="Cost Per Item:").grid(row=5, column=0, sticky='w', pady=5)
        self.lbl_purchase_cost_per_item = ttk.Label(frame, text="GHC 0.00", font=('Arial', 10, 'bold'))
        self.lbl_purchase_cost_per_item.grid(row=5, column=1, sticky='w', pady=5)
        
        btn_add = ttk.Button(frame, text="Record Purchase", command=self.action_add_purchase)
        btn_add.grid(row=6, column=0, columnspan=2, pady=20)

    def on_purchase_product_selected(self, event=None):
        selection = self.cb_purchase_prod.get()
        if selection:
            try:
                prod_id = selection.split("(")[1].split(")")[0]
                last_supplier = inventory.get_last_supplier(prod_id)
                if last_supplier:
                    self.lbl_last_supplier.config(text=f"Last: {last_supplier}")
                    self.ent_purchase_supplier.delete(0, tk.END)
                    self.ent_purchase_supplier.insert(0, last_supplier)
                else:
                    self.lbl_last_supplier.config(text="")
            except:
                self.lbl_last_supplier.config(text="")

    def calc_purchase_cost_per_item(self, event=None):
        try:
            qty = float(self.ent_purchase_qty.get())
            total_cost = float(self.ent_purchase_total_cost.get())
            cost_per_item = total_cost / qty if qty > 0 else 0
            self.lbl_purchase_cost_per_item.config(text=f"GHC {cost_per_item:.2f}")
        except ValueError:
            self.lbl_purchase_cost_per_item.config(text="GHC 0.00")

    def refresh_purchase_products(self):
        products = inventory.get_all_products()
        if not products.empty:
            values = [f"{row['name']} ({row['product_id']})" for _, row in products.iterrows()]
            self.cb_purchase_prod['values'] = values

    def action_add_purchase(self):
        selection = self.cb_purchase_prod.get()
        date_val = self.ent_purchase_date.get()
        supplier = self.ent_purchase_supplier.get()
        qty = self.ent_purchase_qty.get()
        total_cost = self.ent_purchase_total_cost.get()
        
        if not selection or not qty or not total_cost:
            messagebox.showerror("Error", "Product, Quantity, and Total Cost are required.")
            return
            
        try:
            prod_id = selection.split("(")[1].split(")")[0]
            inventory.add_purchase(prod_id, qty, total_cost, supplier, date_val)
            messagebox.showinfo("Success", "Stock added successfully.")
            self.ent_purchase_qty.delete(0, tk.END)
            self.ent_purchase_total_cost.delete(0, tk.END)
            self.ent_purchase_supplier.delete(0, tk.END)
            self.lbl_purchase_cost_per_item.config(text="GHC 0.00")
            self.lbl_last_supplier.config(text="")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # --- Sales Tab ---
    def setup_sales_tab(self):
        frame_left = ttk.Frame(self.tab_sales)
        frame_left.pack(side='left', fill='y', padx=10, pady=10)
        
        ttk.Label(frame_left, text="Customer Name:").pack(anchor='w')
        self.ent_sales_customer = ttk.Entry(frame_left, width=30)
        self.ent_sales_customer.pack(fill='x', pady=5)
        
        ttk.Label(frame_left, text="Select Product:").pack(anchor='w')
        self.cb_sales_prod = ttk.Combobox(frame_left, state="readonly", width=30)
        self.cb_sales_prod.pack(fill='x', pady=5)
        self.cb_sales_prod.bind('<<ComboboxSelected>>', self.on_sales_product_selected)
        
        # Stock info label
        self.lbl_stock_info = ttk.Label(frame_left, text="", foreground='blue')
        self.lbl_stock_info.pack(anchor='w')
        
        ttk.Label(frame_left, text="Quantity:").pack(anchor='w')
        self.ent_sales_qty = ttk.Entry(frame_left, width=30)
        self.ent_sales_qty.pack(fill='x', pady=5)
        
        ttk.Label(frame_left, text="Selling Price Per Item (GHC):").pack(anchor='w')
        self.ent_sales_price = ttk.Entry(frame_left, width=30)
        self.ent_sales_price.pack(fill='x', pady=5)
        
        btn_add_cart = ttk.Button(frame_left, text="Add to Cart", command=self.action_add_to_cart)
        btn_add_cart.pack(pady=10)
        
        btn_clear_cart = ttk.Button(frame_left, text="Clear Cart", command=self.action_clear_cart)
        btn_clear_cart.pack(pady=5)
        
        ttk.Separator(frame_left, orient='horizontal').pack(fill='x', pady=10)
        
        ttk.Label(frame_left, text="Cart Summary", font=('Arial', 11, 'bold')).pack(anchor='w')
        
        self.lbl_cart_subtotal = ttk.Label(frame_left, text="Subtotal: GHC 0.00", font=('Arial', 10))
        self.lbl_cart_subtotal.pack(anchor='w', pady=2)
        
        ttk.Label(frame_left, text="Payment Amount (GHC):").pack(anchor='w', pady=(10, 0))
        self.ent_sales_payment = ttk.Entry(frame_left, width=30)
        self.ent_sales_payment.pack(fill='x', pady=5)
        self.ent_sales_payment.bind('<KeyRelease>', self.update_balance_display)
        
        self.lbl_cart_balance = ttk.Label(frame_left, text="Balance: GHC 0.00", font=('Arial', 10, 'bold'))
        self.lbl_cart_balance.pack(anchor='w', pady=2)
        
        frame_right = ttk.Frame(self.tab_sales)
        frame_right.pack(side='right', fill='both', expand=True, padx=10, pady=10)
        
        ttk.Label(frame_right, text="Cart Items", font=('Arial', 12, 'bold')).pack()
        
        cols = ('S/N', 'ID', 'Name', 'Qty', 'Price', 'Total')
        self.tree_cart = ttk.Treeview(frame_right, columns=cols, show='headings', height=12)
        self.tree_cart.heading('S/N', text='S/N')
        self.tree_cart.column('S/N', width=40)
        self.tree_cart.heading('ID', text='ID')
        self.tree_cart.column('ID', width=60)
        self.tree_cart.heading('Name', text='Name')
        self.tree_cart.column('Name', width=150)
        self.tree_cart.heading('Qty', text='Qty')
        self.tree_cart.column('Qty', width=50)
        self.tree_cart.heading('Price', text='Price')
        self.tree_cart.column('Price', width=80)
        self.tree_cart.heading('Total', text='Total')
        self.tree_cart.column('Total', width=80)
        self.tree_cart.pack(fill='both', expand=True)
        
        btn_checkout = ttk.Button(frame_right, text="Checkout & Generate Invoice", command=self.action_checkout)
        btn_checkout.pack(pady=10)
        
        self.cart_items = []
        self.cart_subtotal = 0.0
        self.current_product_stock = 0

    def on_sales_product_selected(self, event=None):
        """Show stock info when product is selected."""
        selection = self.cb_sales_prod.get()
        if selection:
            try:
                prod_id = selection.split("(")[1].split(")")[0]
                stock = inventory.get_product_stock(prod_id)
                self.current_product_stock = stock
                self.lbl_stock_info.config(text=f"Available Stock: {stock}")
            except:
                self.current_product_stock = 0
                self.lbl_stock_info.config(text="")

    def refresh_sales_product_list(self):
        products = inventory.get_all_products()
        if not products.empty:
            values = [f"{row['name']} ({row['product_id']})" for _, row in products.iterrows()]
            self.cb_sales_prod['values'] = values

    def update_cart_display(self):
        self.cart_subtotal = sum(item['total'] for item in self.cart_items)
        self.lbl_cart_subtotal.config(text=f"Subtotal: GHC {self.cart_subtotal:.2f}")
        self.update_balance_display()

    def update_balance_display(self, event=None):
        try:
            payment = float(self.ent_sales_payment.get())
        except ValueError:
            payment = 0.0
        
        balance = self.cart_subtotal - payment
        if balance < 0:
            self.lbl_cart_balance.config(text=f"Change: GHC {abs(balance):.2f}", foreground='green')
        elif balance > 0:
            self.lbl_cart_balance.config(text=f"Balance Due: GHC {balance:.2f}", foreground='red')
        else:
            self.lbl_cart_balance.config(text="Fully Paid", foreground='green')

    def action_add_to_cart(self):
        selection = self.cb_sales_prod.get()
        qty_str = self.ent_sales_qty.get()
        price = self.ent_sales_price.get()
        
        if not selection:
            messagebox.showerror("Error", "Please select a product.")
            return
        if not qty_str:
            messagebox.showerror("Error", "Please enter quantity.")
            return
        if not price:
            messagebox.showerror("Error", "Please enter selling price per item.")
            return
            
        try:
            prod_id = selection.split("(")[1].split(")")[0]
            prod_name = selection.split(" (")[0]
            qty = int(qty_str)
            
            # Calculate already in cart for this product
            already_in_cart = sum(item['quantity'] for item in self.cart_items if item['product_id'] == prod_id)
            
            # Check stock immediately
            available_stock = inventory.get_product_stock(prod_id)
            total_requested = already_in_cart + qty
            
            if total_requested > available_stock:
                remaining = available_stock - already_in_cart
                messagebox.showerror("Insufficient Stock", 
                    f"Not enough stock for '{prod_name}'.\n\n" +
                    f"Available: {available_stock}\n" +
                    f"Already in cart: {already_in_cart}\n" +
                    f"You can add: {max(0, remaining)}")
                return
            
            unit_price = float(price)
            line_total = unit_price * qty
            
            self.cart_items.append({
                'product_id': prod_id,
                'name': prod_name,
                'quantity': qty,
                'unit_price': unit_price,
                'total': line_total
            })
            
            sn = len(self.cart_items)
            self.tree_cart.insert('', 'end', values=(sn, prod_id, prod_name, qty, f"GHC {unit_price:.2f}", f"GHC {line_total:.2f}"))
            self.ent_sales_qty.delete(0, tk.END)
            self.ent_sales_price.delete(0, tk.END)
            
            self.update_cart_display()
            
            # Update stock display
            self.on_sales_product_selected()
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def action_clear_cart(self):
        self.cart_items = []
        self.cart_subtotal = 0.0
        for item in self.tree_cart.get_children():
            self.tree_cart.delete(item)
        self.ent_sales_customer.delete(0, tk.END)
        self.ent_sales_payment.delete(0, tk.END)
        self.lbl_cart_subtotal.config(text="Subtotal: GHC 0.00")
        self.lbl_cart_balance.config(text="Balance: GHC 0.00", foreground='black')
        self.lbl_stock_info.config(text="")

    def action_checkout(self):
        customer = self.ent_sales_customer.get()
        payment = self.ent_sales_payment.get()
        
        if not customer:
            messagebox.showerror("Error", "Customer Name is required.")
            return
        if not payment:
            messagebox.showerror("Error", "Payment Amount is required.")
            return
        if not self.cart_items:
            messagebox.showerror("Error", "Cart is empty.")
            return
        
        company = inventory.get_company_info()
        if not company.get('name'):
            messagebox.showwarning("Warning", "Company details not set. Please set up in Settings tab.")
            
        try:
            invoice_id, total, balance = inventory.add_sale(customer, self.cart_items, payment)
            
            pdf_filename = invoice_pdf.generate_invoice_pdf(
                invoice_id=invoice_id,
                customer=customer,
                items=self.cart_items,
                total=total,
                payment=float(payment),
                balance=balance,
                date_str=datetime.now().strftime("%Y-%m-%d %H:%M"),
                company_info=company
            )
            
            abs_pdf_path = os.path.abspath(pdf_filename)
            
            msg = f"Invoice {invoice_id} generated!\n\nTotal: GHC {total:.2f}\nPaid: GHC {float(payment):.2f}\nBalance: GHC {balance:.2f}"
            messagebox.showinfo("Success", msg)
            
            try:
                os.startfile(abs_pdf_path)
            except:
                pass
            
            self.action_clear_cart()
            
        except Exception as e:
            messagebox.showerror("Transaction Failed", str(e))

    # --- Debts Tab ---
    def setup_debts_tab(self):
        frame_top = ttk.Frame(self.tab_debts)
        frame_top.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(frame_top, text="Outstanding Debts", font=('Arial', 14, 'bold')).pack()
        
        cols = ('Invoice ID', 'Customer', 'Date', 'Total', 'Paid', 'Balance')
        self.tree_debts = ttk.Treeview(self.tab_debts, columns=cols, show='headings', height=15)
        
        for col in cols:
            self.tree_debts.heading(col, text=col)
            self.tree_debts.column(col, width=120)
        
        self.tree_debts.pack(fill='both', expand=True, padx=10, pady=10)
        
        btn_frame = ttk.Frame(self.tab_debts)
        btn_frame.pack(pady=10)
        
        btn_refresh = ttk.Button(btn_frame, text="Refresh", command=self.refresh_debts_list)
        btn_refresh.pack(side='left', padx=5)
        
        btn_payment = ttk.Button(btn_frame, text="Record Payment", command=self.action_record_payment)
        btn_payment.pack(side='left', padx=5)

    def refresh_debts_list(self):
        for item in self.tree_debts.get_children():
            self.tree_debts.delete(item)
            
        df = inventory.get_debts()
        if not df.empty:
            for _, row in df.iterrows():
                self.tree_debts.insert('', 'end', values=(
                    row['invoice_id'],
                    row['customer_name'],
                    row['date'],
                    f"GHC {row['total']:.2f}",
                    f"GHC {row['paid']:.2f}",
                    f"GHC {row['balance']:.2f}"
                ))

    def action_record_payment(self):
        selected = self.tree_debts.selection()
        if not selected:
            messagebox.showerror("Error", "Please select an invoice.")
            return
        
        item = self.tree_debts.item(selected[0])
        invoice_id = str(item['values'][0])
        balance = float(item['values'][5].replace('GHC ', ''))
        
        amount = simpledialog.askfloat("Record Payment", 
                                       f"Invoice: {invoice_id}\nBalance: GHC {balance:.2f}\n\nEnter payment:",
                                       minvalue=0.01, maxvalue=balance)
        
        if amount:
            try:
                new_balance = inventory.record_payment(invoice_id, amount)
                messagebox.showinfo("Success", f"Payment recorded.\nNew Balance: GHC {new_balance:.2f}")
                self.refresh_debts_list()
            except Exception as e:
                messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = InventoryApp(root)
    root.mainloop()

# Inventory Management System

A simple, offline-capable inventory management system built with Python and Tkinter. Perfect for small businesses to track products, purchases, sales, and debts.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Features

- **Product Management** - Add and manage products with unique IDs (starting from 1000)
- **Purchase/Restock Tracking** - Record stock purchases with supplier info, auto-fills last supplier
- **Sales Processing** - Create sales with custom pricing per item, real-time stock validation
- **PDF Invoice Generation** - Professional invoices with company branding
- **Debt Management** - Track outstanding balances and record payments
- **Company Settings** - Configure company details for invoices
- **Offline Operation** - No internet connection required
- **Standalone EXE** - Bundle as a single executable for easy distribution

## Screenshots

The application includes the following tabs:
- ⚙ Settings - Company configuration
- Inventory Dashboard - View all products and stock levels
- Add Product - Add new products with initial stock
- Restock (Purchase) - Record new stock purchases
- New Sale - Process sales and generate invoices
- Debts & Payments - Manage outstanding balances

## Installation

### Option 1: Run from Source

1. Clone the repository:
```bash
git clone git@github.com:Jake-dev-official/sales-inventory.git
cd sales-inventory
```

2. Install dependencies:
```bash
pip install pandas openpyxl reportlab
```

3. Run the application:
```bash
python gui_app.py
```

### Option 2: Build Standalone EXE

1. Clone the repository and install dependencies (see Option 1)
2. Install PyInstaller:
```bash
pip install pyinstaller
```
3. Build the executable:
```bash
pyinstaller --onefile --windowed --name "InventoryManager" gui_app.py
```
4. Find the exe in the `dist` folder
5. Copy `InventoryManager.exe` anywhere and run it

## Building the Executable

To create a standalone executable:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "InventoryManager" gui_app.py
```

The executable will be created in the `dist` folder.

## Project Structure

```
sales-inventory/
├── gui_app.py          # Main application (Tkinter GUI)
├── inventory.py        # Business logic and operations
├── db_manager.py       # Database operations (Excel)
├── invoice_pdf.py      # PDF invoice generation
├── inventory_database.xlsx  # Data storage (auto-created)
├── invoices/           # Generated PDF invoices
└── dist/
    └── InventoryManager.exe  # Standalone executable
```

## Database Structure

The application uses an Excel file (`inventory_database.xlsx`) with the following sheets:

| Sheet | Purpose |
|-------|---------|
| Products | Product catalog |
| Purchases | Stock-in records |
| Sales | Individual sale line items |
| Invoices | Invoice summaries |
| Payments | Payment records |
| Metadata | App settings |
| History | Deletion logs |

## Usage

### First Time Setup
1. Launch the application
2. Go to Settings tab
3. Enter your company details (name, address, phone, email)
4. Save settings

### Adding Products
1. Go to "Add Product" tab
2. Enter product name
3. Optionally add initial stock (date, supplier, quantity, total cost)
4. Click "Add Product & Stock"

### Making a Sale
1. Go to "New Sale" tab
2. Enter customer name
3. Select product, enter quantity and selling price per item
4. Click "Add to Cart" (stock is validated immediately)
5. Repeat for more items
6. Enter payment amount
7. Click "Checkout & Generate Invoice"

### Recording Payments
1. Go to "Debts & Payments" tab
2. Select an invoice with outstanding balance
3. Click "Record Payment"
4. Enter payment amount

## Currency

The application uses **GHC (Ghana Cedis)** as the currency.

## Requirements

- Python 3.8+
- pandas
- openpyxl
- reportlab

## License

MIT License - Feel free to use and modify for your needs.

## Author

Jake Dev Official

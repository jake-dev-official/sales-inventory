import pandas as pd
import os
from openpyxl import load_workbook

DB_FILE = 'inventory_database.xlsx'
SHEETS = ['Products', 'Purchases', 'Sales', 'Invoices', 'Payments', 'Metadata', 'History']

def initialize_db():
    """Checks if the database exists, creates it if not."""
    if not os.path.exists(DB_FILE):
        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
            for sheet in SHEETS:
                df = pd.DataFrame()
                df.to_excel(writer, sheet_name=sheet, index=False)
        print(f"Database {DB_FILE} created.")
    else:
        # Verify sheets exist
        try:
            xls = pd.ExcelFile(DB_FILE)
            existing_sheets = xls.sheet_names
            with pd.ExcelWriter(DB_FILE, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                for sheet in SHEETS:
                    if sheet not in existing_sheets:
                        pd.DataFrame().to_excel(writer, sheet_name=sheet, index=False)
                        print(f"Sheet {sheet} created.")
        except Exception as e:
            print(f"Error checking database: {e}")

def load_data(sheet_name):
    """Loads a sheet into a DataFrame."""
    try:
        if not os.path.exists(DB_FILE):
            initialize_db()
        return pd.read_excel(DB_FILE, sheet_name=sheet_name)
    except Exception as e:
        print(f"Error loading {sheet_name}: {e}")
        return pd.DataFrame()

def append_data(sheet_name, data_dict):
    """Appends a dictionary of data as a new row to the sheet."""
    try:
        if not os.path.exists(DB_FILE):
            initialize_db()
        
        df = pd.DataFrame([data_dict])
        
        # Load existing workbook to append
        with pd.ExcelWriter(DB_FILE, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            # Check if sheet has data to determine start row
            try:
                reader = pd.read_excel(DB_FILE, sheet_name=sheet_name)
                start_row = len(reader) + 1
                header = False # Don't write header if data exists
                if len(reader) == 0:
                    header = True
                    start_row = 0
            except ValueError:
                # Sheet might be empty or not exist (though init handles existence)
                start_row = 0
                header = True

            df.to_excel(writer, sheet_name=sheet_name, index=False, header=header, startrow=start_row)
            
    except Exception as e:
        print(f"Error appending to {sheet_name}: {e}")
        raise e

def get_metadata(key, default=None):
    """Retrieves a metadata value by key."""
    try:
        metadata = load_data('Metadata')
        if metadata.empty or 'key' not in metadata.columns:
            return default
        row = metadata[metadata['key'] == key]
        if row.empty:
            return default
        return row.iloc[0]['value']
    except Exception as e:
        print(f"Error reading metadata {key}: {e}")
        return default

def set_metadata(key, value):
    """Sets a metadata value. Updates if exists, creates if not."""
    try:
        metadata = load_data('Metadata')
        
        # Check if key exists
        if not metadata.empty and 'key' in metadata.columns and key in metadata['key'].values:
            # Update existing - need to rewrite the whole sheet
            metadata.loc[metadata['key'] == key, 'value'] = value
            # Overwrite the sheet
            with pd.ExcelWriter(DB_FILE, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                metadata.to_excel(writer, sheet_name='Metadata', index=False)
        else:
            # Append new
            append_data('Metadata', {'key': key, 'value': value})
    except Exception as e:
        print(f"Error setting metadata {key}: {e}")
        raise e

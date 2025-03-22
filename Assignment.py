import os
import pandas as pd
from datetime import datetime

def standardize_date(date_str):
    """Convert different date formats to standard datetime."""
    date_formats = ["%d-%m-%Y", "%m-%d-%Y", "%d-%m-%y"]
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

def standardize_amount(amount_str):
    """Convert amount string to a float."""
    if pd.isna(amount_str) or not isinstance(amount_str, str):
        return 0.0
    
    # Remove whitespace and handle special characters
    clean_amount = ''.join(c for c in str(amount_str) if c.isdigit() or c in '.-')
    
    try:
        if 'cr' in str(amount_str).lower():
            return float(clean_amount) * 1e7 if clean_amount else 0.0
        elif 'lakh' in str(amount_str).lower():
            return float(clean_amount) * 1e5 if clean_amount else 0.0
        return float(clean_amount) if clean_amount else 0.0
    except ValueError:
        return 0.0

def detect_file_format(df):
    """Detect the format of input file."""
    first_rows = df.head()
    return {
        'IDFC': any("Transaction Details" in str(row) and len(str(row[0])) > 10 for _, row in first_rows.iterrows()),
        'HDFC': any("Amount" in str(row) for _, row in first_rows.iterrows()),
        'ICICI': any("Domestic Transactions" in str(row) or 
                    (len(row) >= 4 and all(x in str(row) for x in ["Debit", "Credit"]))
                    for _, row in first_rows.iterrows()),
        'AXIS': any("Date" in str(row) and "Transaction Details" in str(row) for _, row in first_rows.iterrows())
    }

def Standardize_Card_Statement(input_file, output_file):
    """Process a single CSV file and handle multiple formats."""
    df = pd.read_csv(input_file, header=None, encoding='utf-8-sig')
    
    # Initialize variables
    current_section = None
    current_card_holder = None
    processed_data = []

    # Detect file format
    file_format = detect_file_format(df)

    for _, row in df.iterrows():
        row_str = ' '.join([str(x) for x in row if pd.notna(x)])
        
        # Section and cardholder detection
        if "Domestic Transactions" in row_str:
            current_section = "Domestic"
            continue
        elif "International Transactions" in row_str or "International Transaction" in row_str:
            current_section = "International"
            continue
        elif any(name in row_str for name in ["Rahul", "Ritu", "Raj", "Rajat"]):
            for name in ["Rahul", "Ritu", "Raj", "Rajat"]:
                if name in row_str:
                    current_card_holder = name
                    break
            continue
        
        try:
            # Skip headers and empty rows
            if row.isna().all() or "Transaction Details" in row_str or "Date" in row_str or "Amount" in row_str:
                continue

            # Extract data based on specific file format
            if file_format['IDFC']:
                # IDFC Format: Transaction Details, Date, Amount
                date = standardize_date(str(row[1]).strip())
                description = str(row[0]).strip()
                amount = standardize_amount(str(row[2])) if pd.notna(row[2]) else 0
                debit = amount if amount > 0 else 0
                credit = abs(amount) if amount < 0 else 0
            
            elif file_format['HDFC']:
                # HDFC Format: Date, Transaction Description, Amount
                date = standardize_date(str(row[0]).strip())
                description = str(row[1]).strip()
                amount = standardize_amount(str(row[2])) if pd.notna(row[2]) else 0
                debit = amount if amount > 0 else 0
                credit = abs(amount) if amount < 0 else 0
            
            elif file_format['AXIS']:
                # AXIS Format: Date, Debit, Credit, Transaction Details
                date = standardize_date(str(row[0]).strip())
                description = str(row[3]).strip() if pd.notna(row[3]) else ""
                debit = float(str(row[1]).strip()) if pd.notna(row[1]) and str(row[1]).strip() else 0
                credit = float(str(row[2]).strip()) if pd.notna(row[2]) and str(row[2]).strip() else 0
            
            elif file_format['ICICI']:
                # Skip non-transaction rows
                if (row.isna().all() or 
                    any(x in row_str for x in ["Domestic Transactions", "International Transaction", "Date", "Debit", "Credit"])):
                    continue

                # Only process rows with valid dates
                if not pd.notna(row[0]) or not str(row[0]).strip():
                    continue

                date = standardize_date(str(row[0]).strip())
                description = str(row[1]).strip() if pd.notna(row[1]) else ""

                # Handle debit amount
                try:
                    debit = standardize_amount(str(row[2])) if pd.notna(row[2]) else 0
                except (ValueError, TypeError):
                    debit = 0

                # Handle credit amount
                try:
                    credit = standardize_amount(str(row[3])) if pd.notna(row[3]) else 0
                except (ValueError, TypeError):
                    credit = 0

                # Skip invalid transactions
                if not description or (debit == 0 and credit == 0):
                    continue
            else:
                raise ValueError("Unknown file format")

            # Extract location and currency
            if description:
                words = description.split()
                if current_section == "Domestic":
                    currency = "INR"
                    location = words[-1].lower() if words else "unknown"
                    description = " ".join(words[:-1]) if words else description
                else:  # International
                    if len(words) > 2:
                        currency = words[-1]  # Last word is currency (EUR/USD)
                        location = words[-2].lower()  # Second last is location
                        description = " ".join(words[:-2])
                    elif len(words) > 1:
                        currency = words[-1]
                        location = "unknown"
                        description = " ".join(words[:-1])
                    else:
                        currency = "Unknown"
                        location = "unknown"

            if description:  # Only add valid transactions
                processed_data.append({
                    "Date": date,
                    "Transaction Description": description.strip(),
                    "Debit": debit,
                    "Credit": credit,
                    "Currency": currency,
                    "CardName": current_card_holder or "Unknown",
                    "Transaction": current_section or "Unknown",
                    "Location": location
                })

        except Exception as e:
            print(f"Error processing row: {row.to_list()}")
            print(f"Error details: {e}")
            continue

    # Create and save DataFrame
    if processed_data:
        output_df = pd.DataFrame(processed_data)
        output_df = output_df[output_df['Date'].notna()]
        output_df.to_csv(output_file, index=False, encoding='utf-8')

def process_all_files(input_dir, output_dir):
    """Process all CSV files in the input directory and write to the output directory."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for file_name in os.listdir(input_dir):
        if file_name.endswith(".csv"):
            input_file = os.path.join(input_dir, file_name)
            output_file_name = file_name.replace("Input", "Output")
            output_file = os.path.join(output_dir, output_file_name)
            print(f"Processing file: {input_file}")
            Standardize_Card_Statement(input_file, output_file)
            print(f"Standardized data written to {output_file}")

def get_valid_path(prompt, check_exists=True):
    """Get a valid file/directory path from user."""
    while True:
        path = input(prompt).strip()
        
        # Remove quotes if user copied path with quotes
        path = path.strip('"\'')
        
        if not path:
            print("Path cannot be empty. Please try again.")
            continue
            
        if check_exists and not os.path.exists(path):
            print(f"Path does not exist: {path}")
            print("Please enter a valid path.")
            continue
            
        return path

if __name__ == "__main__":
    # Get input file path
    input_file = get_valid_path("Enter the path to input CSV file: ", check_exists=True)
    
    # Get output directory path
    output_dir = get_valid_path("Enter the path for output directory: ", check_exists=False)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        except Exception as e:
            print(f"Error creating output directory: {e}")
            exit(1)
    
    # Generate output file path
    output_file = os.path.join(
        output_dir, 
        os.path.basename(input_file).replace("Input", "Output")
    )
    
    try:
        print(f"Processing file: {input_file}")
        Standardize_Card_Statement(input_file, output_file)
        print(f"Standardized data written to: {output_file}")
    except Exception as e:
        print(f"Error processing file: {e}")

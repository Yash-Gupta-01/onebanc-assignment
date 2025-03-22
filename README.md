# Onebanc-assignment
# Credit Card Statement Normalization

## Description
This project aims to standardize credit card statements from various banks into a uniform format. The normalization process involves converting dates to a consistent DateTime format and amounts to a double data type. The goal is to facilitate easier analysis of financial data for users.

## Function Signature
```python
def StandardizeStatement(inputFile: str, outputFile: str) -> None:
```

## Key Features
- Converts dates from multiple formats (DD-MM-YYYY, MM-DD-YYYY, DD-MM-YY) to a standard DateTime format.
- Converts monetary amounts to double data type.
- Processes one input file at a time, generating a corresponding output file.
- Maintains the original file naming convention for output files.

## Input/Output File Naming Convention
- Input File Example: `HDFC-Input-Case1.csv`
- Output File Example: `HDFC-Output-Case1.csv`

## Usage Instructions
1. Place the input CSV files in the `csv file inputs/` directory.
2. Run the `Assignment.py` script to process the files.
3. The output files will be generated in the `outputs/` directory with the same base name as the input files.

## Conclusion
This project provides a robust solution for normalizing credit card statements, making it easier for users to analyze their financial data across different banks. The implementation is designed to be generic and adaptable to various input formats.

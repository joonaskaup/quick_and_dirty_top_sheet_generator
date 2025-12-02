# Quick and Dirty Top Sheet Generator

A lightweight budgeting tool for film & TV production.  
Designed to help you experiment with category amounts, percentage allocations,
and fee structures — and instantly see how changes affect the overall budget.

## Features

- Category-based budgeting with groups  
- Lock Amount / Lock Percentage controls  
- Auto-lock based on last edited field  
- Subtotal and grand total calculation with fees  
- Contingency absorbs rounding differences automatically  
- Change column showing amount deltas after each recalculation  
- Import and export budgets via Excel  
- Clean PySide6 desktop interface  

## Requirements

- Python 3.12+  
- PySide6  
- openpyxl  

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the app

```bash
python main.py
```

## Purpose

This tool is meant for quick iteration when building or adjusting a
top sheet. It provides immediate feedback on how changes cascade through
the budget, without the complexity of a full budgeting suite.


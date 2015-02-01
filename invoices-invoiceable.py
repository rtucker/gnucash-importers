#!/usr/bin/python

import csv
import sys

incsv = csv.DictReader(sys.stdin)
outcsv = csv.writer(sys.stdout)

for row in incsv:
    if int(row['recurring']) == 1:
        continue

    if row['total'] == "100.00":
        desc = "Monthly Invoice - Room"
    elif row['total'] == "50.00":
        desc = "Monthly Invoice - Standard"
    elif row['total'] == "35.00":
        desc = "Monthly Invoice - Student"
    elif row['total'] == "25.00":
        desc = "Monthly Invoice - Associate"
    else:
        desc = "Monthly Invoice - UNKNOWN"

    date = row['date'].split(' ')[0]
    duedate = row['date_due'].split(' ')[0]

    outcsv.writerow([
        "INV" + row['ref'],     # id
        #row['ref'],     # id
        date,                   # date_opened
        row['client_id'],       # owner_id
        "",                     # billingid
        "invoiceable import",                     # notes
        date,                   # date
        desc,                   # desc
        "Material",                 # action
        "Income:Member Dues",   # account
        "1",                    # quantity
        row['total'],           # price
        "", # disc_type
        "", # disc_how
        "",                    # discount
        "", # taxable
        "",                     # taxincluded
        "",                     # tax_table
        date,                   # date_posted
        duedate,                # due_date
        "Assets:Accounts Receivable",   # account_posted
        "", # memo_posted
        "yes",                  # accu_splits
    ])

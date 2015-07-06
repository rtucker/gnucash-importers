#!/usr/bin/python

import csv
import sys

POST_ACCOUNT = "Assets:Accounts Receivable"

incsv = csv.DictReader(sys.stdin)
outcsv = csv.writer(sys.stdout)

for row in incsv:
    if int(row['recurring']) == 1:
        continue

    if row['total'] == "100.00":
        desc = "Monthly Invoice - Desk"
        acct = "Income:Member Dues:Desk"
    elif row['total'] == "50.00":
        desc = "Monthly Invoice - Full"
        acct = "Income:Member Dues:Full"
    elif row['total'] == "35.00":
        desc = "Monthly Invoice - Student"
        acct = "Income:Member Dues:Student"
    elif row['total'] == "25.00":
        desc = "Monthly Invoice - Associate"
        acct = "Income:Member Dues:Associate"
    else:
        desc = "Monthly Invoice - UNKNOWN"
        acct = "Income:Member Dues"

    date = row['date'].split(' ')[0]
    duedate = row['date_due'].split(' ')[0]

    outcsv.writerow([
        "INV" + row['ref'],     # id
        date,                   # date_opened
        row['client_id'],       # owner_id
        "",                     # billingid
        "invoiceable import",   # notes
        date,                   # date
        desc,                   # desc
        "Material",             # action
        acct,                   # account
        "1",                    # quantity
        row['total'],           # price
        "%",                    # disc_type
        "",                     # disc_how
        "0",                    # discount
        "",                     # taxable
        "",                     # taxincluded
        "",                     # tax_table
        date,                   # date_posted
        duedate,                # due_date
        POST_ACCOUNT,           # account_posted
        "",                     # memo_posted
        "yes",                  # accu_splits
    ])

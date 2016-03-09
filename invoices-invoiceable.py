#!/usr/bin/python

from decimal import Decimal
import csv
import sys

POST_ACCOUNT = "Assets:Accounts Receivable"
MAIN_ACCOUNT = "Income:Member Dues"

AMOUNTS = {
    Decimal("100.00"): 'Desk',
    Decimal("50.00"):  'Full',
    Decimal("35.00"):  'Student',
    Decimal("25.00"):  'Associate',
}

TRANSACTION_FEE = Decimal("0.03")   # multiplier

TXN_FEE_AMOUNTS = [f * TRANSACTION_FEE for f in AMOUNTS.keys()]

incsv = csv.DictReader(sys.stdin)
outcsv = csv.writer(sys.stdout)

for row in incsv:
    if int(row['recurring']) == 1:
        continue

    total = Decimal(row['total'])
    txn_fee = Decimal("0.00")

    for k in AMOUNTS.keys():
        for f in TXN_FEE_AMOUNTS:
            if total == (f + k):
                unknown = False
                txn_fee = f
                total -= f

    if total in AMOUNTS:
        desc = "Monthly Dues - " + AMOUNTS[total]
        acct = ":".join([MAIN_ACCOUNT, AMOUNTS[total]])
    else:
        desc = "Monthly Invoice - UNKNOWN"
        acct = "Income:Member Dues"

    date = row['date'].split(' ')[0]
    duedate = row['date_due'].split(' ')[0]

    if txn_fee > Decimal("0.00"):
        outcsv.writerow([
            "INV" + row['ref'],     # id
            date,                   # date_opened
            row['client_id'],       # owner_id
            "",                     # billingid
            "invoiceable import",   # notes
            date,                   # date
            "Payment Processing Surcharge (%g%%)" % (
                TRANSACTION_FEE*Decimal("100.0")),
            "Material",             # action
            MAIN_ACCOUNT + ":Payment Processing Surcharge",
            total,                  # quantity
            TRANSACTION_FEE,        # price
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
        total,                  # price
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

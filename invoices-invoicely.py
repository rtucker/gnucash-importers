#!/usr/bin/python

from datetime import datetime
from decimal import Decimal
from gnucashlib import Gnucash
import csv
import sys

if len(sys.argv) != 2:
    print "usage: %s infile" % sys.argv[0]
    sys.exit(1)

filename = "/home/rtucker/Dropbox/Projects/Interlock/gnucash-prod/interlock-rochester.gnucash"

POST_ACCOUNT = "Assets:Accounts Receivable"
MAIN_ACCOUNT = "Income:Member Dues"

AMOUNTS = {
    Decimal("100.00"): 'Desk',
    Decimal("50.00"):  'Full',
    Decimal("35.00"):  'Student',
    Decimal("25.00"):  'Associate',
}

incsv = csv.DictReader(open(sys.argv[1], 'rb'), dialect="excel-tab")
outcsv = csv.writer(sys.stdout)

with Gnucash(filename) as gc:

    for row in incsv:
        total = Decimal(row['Total'])
        txn_fee = Decimal(row['Tax'])
        dues = total - txn_fee

        if dues in AMOUNTS:
            desc = "Monthly Dues - " + AMOUNTS[dues]
            acct = ":".join([MAIN_ACCOUNT, AMOUNTS[dues]])
        else:
            desc = "Monthly Invoice - UNKNOWN"
            acct = "Income:Member Dues"

        date_dt = datetime.strptime(row['Date Issued'], '%Y %b %d')
        duedate_dt = datetime.strptime(row['Date Due'], '%Y %b %d')

        date = date_dt.strftime('%Y-%m-%d')
        duedate = duedate_dt.strftime('%Y-%m-%d')

        invoiceid = "INV%06d" % Decimal(row['Statement ID'])

        if date_dt < datetime(year=2016,month=5,day=1):
            # avoid old invoices
            continue

        customer = gc.GetCustomerByName(row['Client'])
        if customer is not None:
            clientid = customer.GetID()
        else:
            sys.stderr.write('%s: could not find "%s"\n' % (invoiceid, row['Client']))
            continue

        if txn_fee > Decimal("0.00"):
            outcsv.writerow([
                invoiceid,     # id
                date,                   # date_opened
                clientid,       # owner_id
                "",                     # billingid
                "invoicely import",     # notes
                date,                   # date
                "Payment Processing Surcharge",     # description
                "Material",             # action
                MAIN_ACCOUNT + ":Payment Processing Surcharge",
                dues,                   # quantity
                txn_fee/dues,           # price
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
            invoiceid,     # id
            date,                   # date_opened
            clientid,       # owner_id
            "",                     # billingid
            "invoicely import",     # notes
            date,                   # date
            desc,                   # desc
            "Material",             # action
            acct,                   # account
            "1",                    # quantity
            dues,                   # price
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


#!/usr/bin/python

TESTING=False

import csv
import sys

from datetime import datetime
from decimal import Decimal

from gnucashlib import Gnucash

if len(sys.argv) != 2:
    print "usage: %s infile" % sys.argv[0]
    sys.exit(1)

if TESTING:
    filename = "/home/rtucker/Dropbox/Projects/Interlock/gnucash-test/interlock-rochester-test.gnucash"
else:
    filename = "/home/rtucker/Dropbox/Projects/Interlock/gnucash-prod/interlock-rochester.gnucash"

with Gnucash(filename) as gc:

    from_acct = gc.account("Assets:Current Assets:Dwolla")
    fee_acct = gc.account("Expenses:Bank Service Charge")
    posted_acct = gc.account("Assets:Accounts Receivable")

    # Read in CSV from Dwolla
    incsv = csv.DictReader(open(sys.argv[1], 'rb'))

    for row in incsv:
        if row["Status"] != "processed":
            print("Transaction %s still pending" % row["Id"])
            continue

        date_dt = datetime.strptime(row['Date in Eastern Standard Time'], '%m/%d/%Y %H:%M%p')

        date = date_dt.strftime('%Y-%m-%d')

        num = row['Id']

        description = row['Description']
        notes = "via Dwolla"

        net =   Decimal(row['Amount'].replace(',', '').replace('$',''))
        gross = -net
        fee =   Decimal("0.00")

        # Guess the account
        if net < 0.00:
            # debit
            account = 'Expenses:Miscellaneous'
            if "First Niagara Business Checking" in description:
                account = 'Assets:Current Assets:Checking Account'

        else:
            # credit
            account = 'Income:Other Income'

        to_acct = gc.account(account)

        invoice = None

        if not gc.seen(from_acct, num):
            print "New Transaction:", num, date, description, gross, invoice.GetID() if invoice is not None else 'N/A', account
            newtx = gc.NewTransaction()
            newtx.SetNum(num)
            newtx.SetDate(date_dt.day, date_dt.month, date_dt.year)
            newtx.SetDescription(description)
            newtx.SetNotes(notes)

            s1 = gc.NewSplit(newtx, from_acct, net)
            s2 = gc.NewSplit(newtx, to_acct, gross)

            if invoice is not None:
                # The invoice payment handler is a little bit destructive.
                # So, we do it here before we apply the fee, otherwise
                # an imbalance occurs.
                gc.PayInvoiceWithTransaction(invoice, newtx, from_acct, gross, "Paid via Dwolla", num)
                print "--> Applied to invoice:", invoice.GetID()
                print "    Customer Balance:", invoice.GetOwner().GetBalanceInCurrency(gc.commods['USD'])
            elif net > 0.00 and account is not 'Income:Donations':
                # Try to apply it to a customer
                cname = description.replace("Receive from ", "")
                print "Trying customer:", cname
                customer = gc.GetCustomerByName(cname)
                if customer is not None:
                    gc.ApplyPaymentToCustomer(customer, newtx, posted_acct, from_acct, gross, "Paid via Dwolla", num)
                    print "--> Applied to customer:", customer.GetName()
                    print "    Customer Balance:", customer.GetBalanceInCurrency(gc.commods['USD'])

            s3 = gc.NewSplit(newtx, fee_acct, fee)

            if gc.TransactionReadyToCommit(newtx):
                newtx.CommitEdit()
            else:
                print "ROLLBACK: IMBALANCE"
                newtx.RollbackEdit()
                break

    gc.save()

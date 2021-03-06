#!/usr/bin/python

TESTING=False

import codecs
import csv
import sys

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

    from_acct = gc.account("Assets:Current Assets:PayPal")
    fee_acct = gc.account("Expenses:Bank Service Charge")
    posted_acct = gc.account("Assets:Accounts Receivable")

    # Read in CSV from PayPal
    #incsv = csv.DictReader(open(sys.argv[1], 'rb'), skipinitialspace=True)
    incsv = csv.DictReader(codecs.open(sys.argv[1], 'r', 'utf-8-sig'), skipinitialspace=True)

    for row in incsv:
        if row['Status'] != 'Completed':
            continue

        if row['Type'] == 'Shopping Cart Item':
            continue

        month, day, year = [int(f) for f in row['Date'].split('/')]
        date = '%04d-%02d-%02d' % (year, month, day)

        num = row['Transaction ID']

        description = row['Name']

        notes = row['Type']

        net =   Decimal(row['Net'].replace(',', ''))
        gross = -Decimal(row['Gross'].replace(',', ''))
        fee =   -Decimal(row['Fee'].replace(',', ''))

        # Guess the account
        if net < 0.00:
            # debit
            account = 'Expenses:Miscellaneous'
            if row['Type'] == 'General Withdrawal':
                account = 'Assets:Current Assets:Checking Account'
                description = "Transfer from PayPal to Checking Account"

        else:
            # credit
            account = 'Income:Other Income'
            if row['Item ID'].startswith('INV'):
                account = 'Income:Member Dues'
                notes += ' (%s)' % row['Item ID']
            elif "Donation" in row["Type"]:
                account = 'Income:Donations'

        to_acct = gc.account(account)

        if row['Item ID'] is not "":
            invoice = gc.InvoiceLookupByID(row['Item ID'])
        else:
            invoice = None

        if not gc.seen(from_acct, num):
            print "New Transaction:", num, date, description, gross, invoice.GetID() if invoice is not None else 'N/A', account
            newtx = gc.NewTransaction()
            newtx.SetNum(num)
            newtx.SetDate(day, month, year)
            newtx.SetDescription(description)
            newtx.SetNotes(notes)

            s1 = gc.NewSplit(newtx, from_acct, net)
            s2 = gc.NewSplit(newtx, to_acct, gross)

            if invoice is not None:
                # The invoice payment handler is a little bit destructive.
                # So, we do it here before we apply the fee, otherwise
                # an imbalance occurs.
                gc.PayInvoiceWithTransaction(invoice, newtx, from_acct, gross, "Paid via Invoiceable.com -> PayPal", num)
                print "--> Applied to invoice:", invoice.GetID()
                print "    Customer Balance:", invoice.GetOwner().GetBalanceInCurrency(gc.commods['USD'])

            elif account is 'Income:Other Income' and row['From Email Address'] != "":
                customer = None

                if row['From Email Address'] != "":
                    customer = gc.GetCustomerByEmail(row['From Email Address'])
                if row['Name'] != "" and customer is None:
                    customer = gc.GetCustomerByName(row['Name'])

                if customer is not None:
                    gc.ApplyPaymentToCustomer(customer, newtx, posted_acct, from_acct, gross, "Paid via PayPal", num)
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

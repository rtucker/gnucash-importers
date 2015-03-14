#!/usr/bin/python

TESTING=False

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
    from_acct = gc.account("Assets:Current Assets:Stripe")
    fee_acct = gc.account("Expenses:Bank Service Charge")
    posted_acct = gc.account("Assets:Accounts Receivable")

    # Read in CSV from Square
    incsv = csv.DictReader(open(sys.argv[1], 'rb'), skipinitialspace=True)

    for row in incsv:
        # Created (UTC): yyyy-mm-dd hh:mm
        date = row['Created (UTC)'].split(' ')[0]
        year, month, day = [int(f) for f in date.split('-')]

        num = row['id']

        #description = row['Name']
        description = row['Customer Description']

        notes = row['Statement Descriptor']

        gross = -Decimal(row['Amount'])
        fee =    Decimal(row['Fee'])
        net =   -(gross+fee)

        #print("Gross: $%s" % gross)
        #print("Fee: $%s" % fee)
        #print("Net: $%s" % net)

        # Guess the account
        if net < 0.00:
            # debit
            account = 'Expenses:Miscellaneous'
        #    if row['Name'] == 'Bank Account':
        #        account = 'Assets:Current Assets:Checking Account'
        #    if row['Name'] == 'dennis MAGUIRE':
        #        account = 'Expenses:Rent'

        else:
            # credit
            account = 'Income:Other Income'
        #    if row['Item ID'].startswith('INV'):
        #        account = 'Income:Member Dues'
        #        notes += ' (%s)' % row['Item ID']
        #    elif "Donation" in row["Type"]:
        #        account = 'Income:Donations'
        #    elif "Meraki" in row["Name"]:
        #        account = 'Income:Meraki'

        to_acct = gc.account(account)

        #if row['Item ID'] is not "":
        #    invoice = gc.InvoiceLookupByID(row['Item ID'])
        #else:
        #    invoice = None
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
                gc.PayInvoiceWithTransaction(invoice, newtx, from_acct, gross, "Paid via Invoiceable.co -> Stripe", num)
                print "--> Applied to invoice:", invoice.GetID()
                print "    Customer Balance:", invoice.GetOwner().GetBalanceInCurrency(gc.commods['USD'])
            elif account is not 'Income:Donations':
                # Try to apply it to a customer
                customer = gc.GetCustomerByEmail(row['Customer Email'])
                if customer is not None:
                    gc.ApplyPaymentToCustomer(customer, newtx, posted_acct, from_acct, gross, "Paid via Stripe", num)
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

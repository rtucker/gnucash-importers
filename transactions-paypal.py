#!/usr/bin/python

import csv
import sys

from decimal import Decimal
from gnucash import Session, Transaction, Split, GncNumeric

if len(sys.argv) != 2:
    print "usage: %s infile" % sys.argv[0]
    sys.exit(1)

def account_from_path(top_account, account_path, original_path=None):
    if original_path==None: original_path = account_path
    account, account_path = account_path[0], account_path[1:]

    account = top_account.lookup_by_name(account)
    if account.get_instance() == None:
        raise Exception(
            "path " + ''.join(original_path) + " could not be found")
    if len(account_path) > 0 :
        return account_from_path(account, account_path, original_path)
    else:
        return account

def rat(val):
    s = int(round(val*100))
    return GncNumeric(s, 100)

try:
    session = Session(book_uri="/home/rtucker/Dropbox/Projects/Interlock/gnucash-prod/interlock-rochester.gnucash")
    #session = Session(book_uri="/home/rtucker/Dropbox/Projects/Interlock/gnucash-test/interlock-rochester-test.gnucash")
    book = session.book
    root_account = book.get_root_account()

    commod_tab = session.book.get_table()
    USD = commod_tab.lookup("ISO4217","USD")

    from_acct = account_from_path(root_account, "Assets:Current Assets:PayPal".split(':'))

    fee_acct = account_from_path(root_account, "Expenses:Bank Service Charge".split(':'))

    seen_nums = []

    for split in from_acct.GetSplitList():
        txn = split.parent
        if txn.GetNum() not in seen_nums:
            seen_nums.append(txn.GetNum().strip())

    incsv = csv.DictReader(open(sys.argv[1], 'rb'), skipinitialspace=True)

    for row in incsv:
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
            if row['Name'] == 'Bank Account':
                account = 'Assets:Current Assets:Checking Account'
            if row['Name'] == 'dennis MAGUIRE':
                account = 'Expenses:Rent'

        else:
            # credit
            account = 'Income:Other Income'
            if row['Item ID'].startswith('INV'):
                account = 'Income:Member Dues'
                notes += ' (%s)' % row['Item ID']

        to_acct = account_from_path(root_account, account.split(':'))

        if row['Item ID'] is not "":
            invoice = book.InvoiceLookupByID(row['Item ID'])
            #invoice = book.InvoiceLookupByID("000001")
        else:
            invoice = None

        if num.strip() not in seen_nums:
            print num, date, description, gross, invoice
            newtx = Transaction(book)
            newtx.BeginEdit()
            newtx.SetCurrency(USD)
            newtx.SetNum(num)
            newtx.SetDate(day, month, year)
            newtx.SetDescription(description)
            newtx.SetNotes(notes)

            s1 = Split(book)
            s1.SetParent(newtx)
            s1.SetAccount(from_acct)
            s1.SetAmount(rat(net))
            s1.SetValue(rat(net))
            s2 = Split(book)
            s2.SetParent(newtx)
            s2.SetAccount(to_acct)
            s2.SetAmount(rat(gross))
            s2.SetValue(rat(gross))

            if invoice is not None:
                invoice.BeginEdit()
                invoice.ApplyPayment(newtx, from_acct, rat(-gross), rat(1), newtx.RetDatePostedTS(), "Imported from PayPal", num)
                invoice.CommitEdit()

            s3 = Split(book)
            s3.SetParent(newtx)
            s3.SetAccount(fee_acct)
            s3.SetAmount(rat(fee))
            s3.SetValue(rat(fee))

            imb = newtx.GetImbalanceValue()

            print "  imbalance: %s" % imb

            print "  balanced? %s" % newtx.IsBalanced()

            for split in newtx.GetSplitList():
                if split.GetValue().to_double() == 0.0:
                    split.Destroy()

            if not newtx.IsBalanced():
                for (commod, val) in newtx.GetImbalance():
                    print val.to_string(), commod.get_mnemonic()

                print "ROLLBACK"
                newtx.RollbackEdit()
                break
            else:
                print "COMMIT"
                newtx.CommitEdit()

    session.save()

finally:
    if "session" in locals():
        session.end()


from gnucash import Session, GncNumeric, Transaction, Split, Query
from gnucash.gnucash_business import Customer

class Gnucash:
    __seendict = {}

    def __init__(self, book_uri):
        self._session = Session(book_uri=book_uri)
        self._book = self._session.book
        self._root_account = self._book.get_root_account()

        self._commodity_table = self._book.get_table()

        # todo: implement as class w/ getattr
        self.commods = {}
        self.commods['USD'] = self._commodity_table.lookup("ISO4217", "USD")

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._session.end()

    def save(self):
        self._session.save()

    def seen(self, acct, num):
        if repr(acct) not in self.__seendict:
            l = []
            for split in acct.GetSplitList():
                txn = split.parent
                if txn.GetNum() not in l:
                    l.append(txn.GetNum().strip())
            self.__seendict[repr(acct)] = l

        return num in self.__seendict[repr(acct)]

    def _account_from_path(self, top_account, account_path, original_path=None):
        if original_path==None: original_path = account_path
        account, account_path = account_path[0], account_path[1:]

        account = top_account.lookup_by_name(account)
        if account.get_instance() == None:
            raise Exception(
                "path " + ''.join(original_path) + " could not be found")
        if len(account_path) > 0 :
            return self._account_from_path(account, account_path, original_path)
        else:
            return account

    def account(self, account_path):
        return self._account_from_path(self._root_account, account_path.split(':'))

    def rat(self, value):
        s = int(round(value*100))
        return GncNumeric(s, 100)

    def NewTransaction(self):
        t = Transaction(self._book)
        t.BeginEdit()
        t.SetCurrency(self.commods['USD'])
        return t

    def NewSplit(self, txn, acct, amount):
        s = Split(self._book)
        s.SetParent(txn)
        s.SetAccount(acct)
        s.SetAmount(self.rat(amount))
        s.SetValue(self.rat(amount))
        return s

    def TransactionReadyToCommit(self, txn):
        for split in txn.GetSplitList():
            if split.GetValue().to_double() == 0.0:
                split.Destroy()

        return txn.IsBalanced()

    def InvoiceLookupByID(self, id):
        return self._book.InvoiceLookupByID(id)

    def PayInvoiceWithTransaction(self, invoice, txn, acct, gross, memo, num):
        invoice.BeginEdit()
        invoice.ApplyPayment(txn, acct, self.rat(-gross), self.rat(1), txn.RetDatePostedTS(), memo, num)
        invoice.CommitEdit()

    def ApplyPaymentToCustomer(self, customer, txn, post_acct, from_acct, gross, memo, num):
        customer.BeginEdit()
        customer.ApplyPayment(txn, None, post_acct, from_acct, self.rat(-gross), self.rat(1), txn.RetDatePostedTS(), memo, num, True)
        customer.CommitEdit()

    def GetCustomerByEmail(self, email):
        q = Query()
        q.search_for('gncCustomer')
        q.set_book(self._book)

        c = None

        for result in q.run():
            tmp = Customer(instance=result)
            if tmp.GetAddr().GetEmail().lower() == email.lower():
                c = tmp
                break

        q.destroy()

        return c

    def GetCustomerByName(self, name):
        q = Query()
        q.search_for('gncCustomer')
        q.set_book(self._book)

        c = None

        for result in q.run():
            tmp = Customer(instance=result)
            if tmp.GetName().lower() in name.lower():
                c = tmp
                break

        q.destroy()

        return c


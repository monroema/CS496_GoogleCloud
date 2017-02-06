from google.appengine.ext import ndb
import webapp2
import json


### Global Methods ###
def get_entity(p_id):
    return ndb.Key(urlsafe=p_id).get()


def string_to_bool(p_string):
    if p_string == '':
        return None
    elif p_string.lower() == 'true':
        return True
    elif p_string.lower() == 'false':
        return False
    else:
        return 'ERROR'


class Customers(ndb.Model):
    name = ndb.StringProperty(required=True)
    balance = ndb.FloatProperty(default=0.0)
    checked_out = ndb.StringProperty(repeated=True)


class CustomersHandler(webapp2.RequestHandler):
    def post(self):
        customers_data = json.loads(self.request.body)
        if customers_data['checked_out'] is None or customers_data['checked_out'] == '':
            customers_data['checked_out'] = ''
        new_customer = Customers(
            name=customers_data['name'],
            balance=customers_data['balance'],
            checked_out=customers_data['checked_out'])
        new_customer.put()
        customers_dict = new_customer.to_dict()
        customers_dict['id'] = new_customer.key.urlsafe()
        customers_dict['self'] = '/customers/' + new_customer.key.urlsafe()
        self.response.write(json.dumps(customers_dict))

    def get(self, id=None):
        if id is not None:
            customer = get_entity(id)
            customer_dict = customer.to_dict()
            customer_dict['id'] = id
            customer_dict['self'] = '/customers/' + id
            self.response.write(json.dumps(customer_dict))
        else:
            query_customer = Customers.query()
            customer_list = query_customer.fetch()
            results = []
            for entity in customer_list:
                single_customer = entity.to_dict()
                single_customer['id'] = entity.key.id()
                single_customer['self'] = '/customers/' + str(entity.key.id())
                results.append(single_customer)
            self.response.write(json.dumps(results))

    def patch(self, id=None):
        if id is not None:
            customer = get_entity(id)
            properties = json.loads(self.request.body)
            if 'name' in properties:
                customer.name = properties['name']
            if 'balance' in properties:
                customer.balance = properties['balance']
            if 'checked_out' in properties:
                customer.checked_out = properties['checked_out']
            customer.put()
            book_dict = customer.to_dict()
            book_dict['id'] = customer.key.id()
            book_dict['self'] = '/books/' + customer.key.urlsafe()
            self.response.write(json.dumps(book_dict))

    def delete(self, id=None):
        query_customer = get_entity(id)
        query_customer.key.delete()


class Books(ndb.Model):
    title = ndb.StringProperty(required=True)
    isbn = ndb.StringProperty(required=True)
    genre = ndb.JsonProperty(required=True)
    author = ndb.StringProperty(required=True)
    checkedIn = ndb.BooleanProperty(required=True)


class BooksHandler(webapp2.RequestHandler):
    def post(self):
        books_data = json.loads(self.request.body)
        new_book = Books(
            title=books_data['title'],
            isbn=books_data['isbn'],
            genre=books_data['genre'],
            author=books_data['author'],
            checkedIn=books_data['checkedIn'])
        new_book.put()
        books_dict = new_book.to_dict()
        books_dict['id'] = new_book.key.urlsafe()
        books_dict['self'] = '/books/' + new_book.key.urlsafe()
        self.response.write(json.dumps(books_dict))

    def get(self, id=None):
        if id is not None:
            book = get_entity(id)
            book_dict = book.to_dict()
            self.response.write(json.dumps(book_dict))
        else:
            book_status_filter = string_to_bool(self.request.get('checkedIn'))
            if book_status_filter is not None and book_status_filter != u'ERROR':
                query_book = Books.query(Books.checkedIn == book_status_filter)
            elif book_status_filter is None:
                query_book = Books.query()
            else:
                self.response.write('ERROR')
            book_list = query_book.fetch()
            back_data = []
            for book in book_list:
                book_dict = book.to_dict()
                book_dict['id'] = book.key.id()
                back_data.append(book_dict)
                book_dict['self'] = '/books/' + book.key.urlsafe()
            self.response.write(json.dumps(back_data))

    def patch(self, id=None):
        if id is not None:
            book = get_entity(id)
            properties = json.loads(self.request.body)
            if 'title' in properties:
                book.title = properties['title']
            if 'isbn' in properties:
                book.isbn = properties['isbn']
            if 'author' in properties:
                book.author = properties['author']
            if 'genre' in properties and properties['genre'] not in book.genre:
                book.genre.append(properties['genre'])
            if 'checkedIn' in properties:
                book.checkedIn = properties['checkedIn']
            book.put()
            book_dict = book.to_dict()
            book_dict['id'] = book.key.id()
            book_dict['self'] = '/books/' + book.key.urlsafe()
            self.response.write(json.dumps(book_dict))

    def delete(self, id=None):
        if id is not None:
            get_entity(id).key.delete()


class CheckInOut(webapp2.RequestHandler):
    def put(self, *args):
        customer_id = args[0]
        customers = get_entity(customer_id)
        book_id = args[1]
        books = get_entity(book_id)
        books.checkedIn = False
        books.put()
        customers.checked_out.append('/books/' + book_id)
        customers.put()

    def get(self, *args):
        customer_id = args[0]
        customers = get_entity(customer_id)
        book_id = args[1]
        if any(book_id in s for s in customers.checked_out):
            books = get_entity(book_id)
            book = books.to_dict()
            book['id'] = book_id
            self.response.write(json.dumps(book))

    def delete(self, *args):
        customer_id = args[0]
        customers = get_entity(customer_id)
        book_id = args[1]
        books = get_entity(book_id)
        books.checkedIn = True
        books.put()
        customers.checked_out.remove('/books/' + book_id)
        customers.put()


class CheckedOutHandler(webapp2.RequestHandler):
    def get(self, id=None):
        customer_id = id
        customer = get_entity(customer_id)
        cust_dict = customer.to_dict()
        books_checked_out = cust_dict['checked_out']
        results = []
        for book in books_checked_out:
            book = CheckedOutHandler.url_string_maker(book)
            book = get_entity(book)
            book_d = book.to_dict()
            results.append(book_d)
        self.response.write(json.dumps(results))

    @staticmethod
    def url_string_maker(book_str):
        return book_str.replace('/books/', '').replace(' ', '').replace('[', '').replace(']', '') \
            .replace('u\'', '').replace('\'', '')


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.write('Main Page, there shouldn\'t be anything here right now!')

    def delete(self):
        ndb.delete_multi(Books.query().fetch(keys_only=True))
        ndb.delete_multi(Customers.query().fetch(keys_only=True))


allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/customers/(.*)/books/(.*)', CheckInOut),
    ('/customers/(.*)/books', CheckedOutHandler),
    ('/customers', CustomersHandler),
    ('/customers/(.*)', CustomersHandler),
    ('/books', BooksHandler),
    ('/books/', BooksHandler),
    ('/books/(.*)', BooksHandler)
], debug=True)

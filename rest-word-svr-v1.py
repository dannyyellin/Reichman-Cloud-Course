# This is example REST API server code for lecture: topic-2 REST
# It uses Flask to build a RESTful service in Python.
# A good introduction is https://towardsdatascience.com/the-right-way-to-build-an-api-with-python-cd08ab285f8f
# See also https://dzone.com/articles/creating-rest-services-with-flask
# To run this program, in terminal window issue the cmd:
#   python3 rest-word-svr-v1.py
# alternatively, comment out "app.run..." cmd in __main__ and issue the following cmds
#   export FLASK_APP-"rest-word-svr-v1.py"
#   flask run --port 8000     (or whatever port you want to run on.  if no "--port" option specified, it is port 5000)
# flask will return the IP and port the app is running on
# you must install the packages Flask and flask-restful before running this program

# The resources are:
# /words         These are the collection of words in the collection.  Each word has a unique key
# /words/total   This is the total number of words in the collection.  It is an integer
# /words/{key}   This is a specific word given by its key

# The supported operations on each of these resources are:
# /words:
#   POST (add a word, the key for this word is returned),
#   GET (get the entire collection of words, together with their keys)
# /words/total:
#   GET (gets the integer equal to the total number of words in a collection)
# /words/keys/{key}:
#   GET (gets the word associated with a given key)
#   DELETE (delete a word with a given key)
#   PUT (replace a word with a given key with another word)

from flask import Flask  # , jsonify
from flask_restful import Resource, Api, reqparse

app = Flask(__name__)  # initialize Flask
api = Api(app)  # create API


# wordCollection class stores the words and perform operations on them
class WordCollection:
    def __init__(self):
        # self.opNum is the number of insertWord operations performed so far.
        # It will be used to generate unique keys to words inserted into collection
        self.opNum = 0
        # self.wrds is a dictionary of the form {key:word} where key is an integer and word is a string
        self.wrds = {}  # Words in the collection

    def insertWord(self, w):
        # This function SHOULD CHECK if word already exists and if so return error.
        # Currently, it lets the same word exist with different keys
        if w in self.wrds.values():  # word already exists
            print("WordCollection: word ", w, " already exists")
            return 0  # key = 0 indicates cannot be inserted
        self.opNum += 1
        key = self.opNum
        self.wrds[key] = w
        print("WordCollection: inserted word ", w, " with key ", key)
        return key

    def delWord(self, key):
        if key in self.wrds.keys():  # the key exists in collection
            w = self.wrds[key]
            del self.wrds[key]
            print("WordCollection: deleted word ", w, " with key ", key)
            return True, w
        else:
            return False, None  # the key does not exist in the collection

    def findWord(self, key):
        if key in self.wrds.keys():  # the key exists in collection
            w = self.wrds[key]
            print("WordCollection: found word ", w, " with key ", key)
            return True, w
        else:
            print("WordCollection: did not find key", key)
            return False, None  # the key does not exist in the collection

    def replaceWord(self, key, newWord):
        if key in self.wrds.keys():  # the key exists in collection
            self.wrds[key] = newWord
            print("WordCollection: New word for key ", key, " is ", newWord)
            return True, newWord
        else:  # the key does not exist in the collection
            print("WordCollection: did not find key", key)
            return False, None

    def collSize(self):
        print("WordCollection: collection size = ", str(len(self.wrds)))
        return len(self.wrds)

    # retrieveAll returns all the dictionary containing all words
    def retrieveAllWords(self):
        print("WordCollection: retrieving all words:")
        print(self.wrds)
        return self.wrds


col = WordCollection()    # create WordCollection instance with global scope


# The Words class implements the REST operations for the /words resource
class Words(Resource):
    global col

    # POST adds a word to /words and returns its key.
    def post(self):
        # get argument being passed in query string
        parser = reqparse.RequestParser()  # initialize parse
        # in the query_string, expect "?word=w" where w is the word to be added
        parser.add_argument('word', location='args', required=True)  # location='args' is required, at least on macOS
        args = parser.parse_args()  # parse arguments into a dictionary structure
        w = args["word"]
        # add w to collection
        key = col.insertWord(w)
        if key == 0:   # word already exists
            return key, 422
        return key, 201

    # GET returns all the words in the collection in json
    def get(self):
        # return jsonify(col.retrieveAllWords())
        # flask will automatically jsonify a dictionary so the above line is not needed
        return col.retrieveAllWords(), 200


# The Key class implements the REST operations for the /words/{KEY} resource
class Key(Resource):
    # Note that for Key class, the key will be supplied to all requests as a parameter
    global col

    # DELETE deletes a word from the collection
    def delete(self, key):
        # delete word from collection
        b, w = col.delWord(key)
        if b:
            return w, 200  # return deleted word and HTTP 200 ok code
        else:
            return 0, 404  # return 0 for key value (error) and Not Found error code

    # GET retrieves a specific word from the collection
    def get(self, key):
        (b, w) = col.findWord(key)
        if b:
            return w, 200  # return the word and HTTP 200 ok code
        else:
            return 0, 404  # return 0 for key and Not Found error code

    # PUT modifies a word associated with a specific key
    def put(self, key):
        # get argument being passed in query string (the word to replace the existing word with this key)
        # in the query_string, "?word=w" where w is the word to replace the existing word
        parser = reqparse.RequestParser()  # initialize parse
        parser.add_argument('word', location='args', required=True)  # location='args' is required, at least on macOS
        args = parser.parse_args()  # parse arguments to dictionary
        newWord = args["word"]
        # replace the word in the collection
        b, w = col.replaceWord(key, newWord)
        if b:
            return w, 200  # return the word and HTTP 200 ok code
        else:
            return 0, 404  #return 0 for key and Not Found error code


# The Count class implements the REST operations for the /words/total resource
class Count(Resource):
    global col

    # GET retrieves the size of the collection
    def get(self):
        return col.collSize(), 200


# associate the Resource '/words' with the class Words
# associate the Resource '/words/key' with the class Key
# associate the Resource '/words/total' with the class Count
api.add_resource(Words, '/words')
api.add_resource(Key, '/words/<int:key>')
api.add_resource(Count, '/words/total')

if __name__ == '__main__':
    # create collection dictionary and keys list
    print("running rest-word-svr-v1.py")
    # run Flask app.   default part is 5000
    app.run(host='0.0.0.0', port=8000, debug=True)

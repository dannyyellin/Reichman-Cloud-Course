# This is example of enhancing our REST API server code for lecture: topic-5-High Availability
# rest-word-svr-v3.py augments the previous example (rest-word-svr-v2.py), in a few ways:
# - it stores its data (the word) collection in a persistence store (MongoDB).  MongoDB is running in another container.
# - it is configured to restart if it fails.   since the data is in a persistence store, no data is lost.  but care
# must be taken to recover the data needed properly.
# - Other changes to this program are configured in the docker-compose-persist.yml file.
# - nginx is running in another container.   NGINX will only give access to regular users on port 80 and will restrict
#  the operation they can perform to GET requests.
#
# since the application may crash, we need a way to know what ID to use when inserting a new doc into the collection.
# algorithm 1:
# don't store the current key in mongo.   instead, check and see if the collection is empty.  if yes, then
# no docs in the collection yet & set the new key = 1. otherwise, find the highest numbered doc in the collection. say
# that its "_id" field has value X.  then set the new key = X+1.  finding the highest numbered record is implemented by
# cur_key = wordscoll.find_one(sort=[("_id", -1)])["_id"]   # Sort by "_id" field (descending values) & return first doc
# (see https://dba.stackexchange.com/questions/108113/how-to-get-minimum-value-in-pymongo)
# algorithm 2:
# if you have a large collection, algorithm 1 (sorting all docs) can be expensive.   instead a simpler technique is to
# store a special doc in the collection with _id==0 and with a field name "cur_key".  the value of the "cur_key" field
# is the value of the _id of last doc inserted into the collection.   when starting up, check if any record with
# _id == 0 is in the # collection.  if not, insert this record into the collection.   whenever inserting a new record
# into the collection, retrieve the cur_key value, update its value in mongo, and use this updated value for the _id
# field of the new doc.  using
# this algorithm means that there is one doc in the collection that is different from the others - the one containing
# the field "cur_key".   care must be taken to filter out this record when retrieving all word docs in the collection.
#
# Note: this implementation differs from rest-word-svr-v2.py in that GET returns a JSON array of words, instead of a
# JSON object indexed by the word ID.    Can easily change it to return JSON object if desired.
# This implementation of PUT specifies the word to replace a given word is provided in the query string.  A more correct
# implementation would specify the replacement word in a JSON object.   I have left it as part of the query string for
# now to illustrate the use of the FLASK "reqparse", which retrieves values from the query string
#
import json
import sys
import os, signal

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

from flask import Flask, request  # , jsonify
from flask_restful import Api, reqparse
import pymongo

app = Flask(__name__)  # initialize Flask
api = Api(app)  # create API

# initialization of Mongo client.  docker-compose is configured to that this program only starts up after Mongo is up
# and running.
client = pymongo.MongoClient("mongodb://mongo:27017/")
# Warning:  do not use client = pymongo.MongoClient("mongodb://localhost:27017/") as docker-compose assigns mongo a
# unique address to the container.  In the following, db is the name of the database and wordscoll: is the name of the
# collection (e.g., table) in the db where the words will be stored.
# each document (except for cur_key) in the wordscoll collection is of the form {"_id": _id, "value": word}
db = client["wordsdb"]
wordscoll = db["words"]
# check if this is the first time starting up; i.e., do we already have a record with _id == 0 in the collection or not.
# If it does, do nothing.  if not, initialize
if wordscoll.find_one({"_id": 0}) is None:  # first time starting up this service as no document with _id ==0 exists
    # insert a document into the database to have one "_id" index that starts at 0 and a field named "cur_key"
    wordscoll.insert_one({"_id": 0, "cur_key": 0})
    print("Inserted document containing cur_key with _id == 0 into the collection")
    sys.stdout.flush()


# POST adds a word to /words and returns its key.
@app.route('/words', methods=['POST'])
def post_word():
    content_type = request.headers.get('Content-Type')
    if content_type != 'application/json':
        return "Expected 'application/json' content_type", 415  # 415 Unsupported Media Type
    try:
        data = request.get_json()  # retrieves the json content of the request, assumes content type is application/json
        # ! perform error handling if the not JSON content type
        word = data["word"]  # assumes that json content is {"word": w} where w is the word (a string)
    except KeyError:  # no such parameter "word"
        print("POST /words exception: 'word' parameter not supplied")
        sys.stdout.flush()
        return -1, 422
    else:  # found parameter word, query mongo for the word
        doc = wordscoll.find_one({"value": word})
        if doc is not None:
            print(word + " already exists in Mongo with key " + str(doc["_id"]))
            sys.stdout.flush()
            return word + " already exists in Mongo with key " + str(doc["_id"]), 404
        docID = {"_id": 0}  # doc containing cur_key has the value of 0 for its "_id" field
        # retrieve the doc with "_id" value = 0 and extract the "cur_key" value from it and increment its value
        cur_key = wordscoll.find_one(docID)["cur_key"] + 1
        # set the "cur_key" field of the doc that meets the docID constraint to the updated value cur_key
        result = wordscoll.update_one(docID, {"$set": {"cur_key": cur_key}})
        result = wordscoll.insert_one({"_id": cur_key, "value": word})
        print("inserted " + word + " into mongo with ID " + str(result.inserted_id))
        print(result)
        sys.stdout.flush()
        return "inserted " + word + " into mongo with ID " + str(result.inserted_id) + "\n", 200


# GET returns all the words in the collection in json
# ! implement GET with possible query string that states to get only words starting with a specific letter
@app.route('/words', methods=['GET'])
def get_all():
    # return documents whoose "_id" field >= 1.
    # See https://www.oreilly.com/library/view/mongodb-the-definitive/9781449344795/ch04.html
    cursor = wordscoll.find({"_id": {"$gte": 1}})
    # cursor is a pymongo cursor object.  iterate over the result to see all the documents
    print("list of all words:")
    sys.stdout.flush()
    if cursor is not None:   # iterate over cursor.   one you iterate, the cursor is at the end of the list
        for doc in cursor:
            print(doc)
            sys.stdout.flush()
    # !! need to check for error
    print("mongo retrieved all words")
    # online info:
    # you can perform a find() query on a collection and get a cursor object. you can then iterate over the
    # cursor & do something with each document (e.g., just print it). After you're finished iterating over the
    # cursor, you call the rewind() method to reset the cursor to the beginning of the result set. You can then iterate
    # over the cursor again and do something else with each document.
    # Note that rewinding a cursor can be an expensive operation if there are a large number of documents in the result
    # set, because it requires the server to re-execute the query.  For this reason, it's generally a good practice to
    # try to avoid rewinding cursors if possible, and instead process the result set in a single pass.
    cursor.rewind()
    cursor_list = list(cursor)    # convert cursor object into list
    print("list(cursor) =")
    print(cursor_list)
    sys.stdout.flush()
    cursor_json = json.dumps(cursor_list)     # convert list to JSON array
    return cursor_json, 200


# DELETE deletes a word from the collection
@app.route('/words/<int:key>', methods=['DELETE'])
def delete_word(key):
    doc = wordscoll.find_one({'_id': key})
    if doc is None:   # did not find the document with that key in the collection
        return "key " + str(key) + " not found and word not deleted", 404
    else:
        w = doc['value']   # w is the word being deleted
    result = wordscoll.delete_one({'_id': key})
    print("delete_word: result.acknowledged=")
    print(result.acknowledged)
    print("delete_word: result.deleted_count=")
    print(result.deleted_count)
    sys.stdout.flush()
    if result.acknowledged and result.deleted_count >= 1:  # if result was deleted
        print("deleted word with key ", str(key))
        sys.stdout.flush()
        return "Deleted word " + w + " with key " + str(key), 200  # return deleted word and HTTP 200 ok code
    else:  # something went wrong
        print("mongo failed to delete word with key ", str(key))
        sys.stdout.flush()
        return w + " with key " + str(key) + " was not deleted", 404


# GET retrieves a specific word from the collection
@app.route('/words/<int:key>', methods=['GET'])
def get_word(key):
    doc = wordscoll.find_one({"_id": key})
    if doc is None:
        print("mongo did not find ", key, "in findWord method")
        sys.stdout.flush()
        return "key " + str(key) + " was not found", 404
    else:
        print("mongo found ", doc, " for key ", key)
        sys.stdout.flush()
        w = doc["value"]
        print("mongo found word ", w, " with key ", str(key))
        sys.stdout.flush()
        return "word with key " + str(key) + " is " + w, 200


# GET retrieves the size of the collection
@app.route('/words/total', methods=['GET'])
def get():
    # retrieve total number of docs in collection and subtract 1 for special "cur_key" doc
    total = wordscoll.count_documents({}) - 1
    return "total number of words in collection is " + str(total), 200


@app.route('/words/<int:key>', methods=['PUT'])
def put(key):
    # get argument being passed in query string (the word to replace the existing word with this key)
    # in the query_string, "?word=w" where w is the word to replace the existing word
    try:
        parser = reqparse.RequestParser()  # initialize parse
        parser.add_argument('word', location='args', required=True)  # location='args' is required, at least on macOS
        args = parser.parse_args()  # parse arguments to dictionary
        newWord = args["word"]
    except:  # "word" not provided in query string
        return -1, 422
    doc_existing = wordscoll.find_one({"_id": key})  # check that key of word to be updated exists in collection
    if doc_existing is None:
        print("mongo did not find the key ", str(key))
        sys.stdout.flush()
        return "key ", str(key), " was not found, PUT not executed", 404
    else:  # check that new word does not already exist in collection
        doc_new = wordscoll.find_one({"value": newWord})
        if doc_new is not None:
            print(newWord + " already exists in Mongo with key " + str(doc_new["_id"]))
            sys.stdout.flush()
            return newWord + " already exists in Mongo with key " + str(doc_new["_id"]), 404
    # update the collection so that the "value" field of the doc with _id = key is set to newWord
    result = wordscoll.update_one({"_id": key}, {"$set": {"value": newWord}})
    return "word with key " + str(key) + " updated to " + newWord, 200


if __name__ == '__main__':
    # create collection dictionary and keys list
    print("running OLD rest-word-svr-v3.py")

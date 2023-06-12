import sys

import connectionController
from assertions import *

word_collection = {}

# tests for dish API

def test_words_empty():
    response = connectionController.http_get("words")
    assert response.status_code == 200
    assert response.json() == {}

def test_insert_word1():
    word = "house"
    response = connectionController.http_post_qs("words",word)
    assert_valid_added_resource(response)
    word_collection[response.json()] = "house"

def test_get_word_by_id():
    word = "book"
    response = connectionController.http_post_qs("words",word)
    assert_valid_added_resource(response)
    book_id = response.json()
    word_collection[book_id] = "book"
    response = connectionController.http_get(f"words/{book_id}")
    assert_status_code(response, status_code=200)
    assert response.json() == "book"

def test_add_exists_word():
    word = "house"
    response = connectionController.http_post_qs("words", word)
    assert_status_code(response, status_code=422)
    assert_ret_value(response, 0)


def test_get_not_exists_word_id():
    NOT_EXISTS_WORD_ID = 11235
    response = connectionController.http_get(f"words/{NOT_EXISTS_WORD_ID}")
    assert_status_code(response, status_code=404)
    assert_ret_value(response, returned_value=0)

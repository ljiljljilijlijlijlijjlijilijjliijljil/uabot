import personal_data
from pymongo import MongoClient


# ======= BASIC ACCESS DATABASE ======
# This function is used in every database query, as it follows to our Uabot DataBase
# and returns the MongoDB object, through which we can follow
def receive_database():
    connection_string = "mongodb+srv://" + str(personal_data.get_login()) + ":" + str(personal_data.get_password()) +\
                        "@petprojectsx-c0xb2.mongodb.net/<dbname>?retryWrites=true&w=majority"
    client = MongoClient(connection_string)
    db = client.uabot
    return db


# ====== ADD COLLECTION TO MONGODB ======
# Add the dictionary, that is added as an argument to index_data collection.
def insert_dictionary(dictionary):
    db = receive_database()
    index_data = db.index_data
    i = 1
    for x in dictionary:
        if i == len(dictionary) + 1:
            break
        this_id = "id" + str(i)
        item = dictionary[this_id]
        address = item["address"]
        index = item["index"]
        city = item['city']
        item_dictionary = {"address": address, "index": index, "city": city}
        index_data.insert_one(item_dictionary)
        i += 1
    return "OK"


# ============ FIND THE INDEX IN THE COLLECTION BY REQUEST ======
# This function follows through the index data collection and receives string
# Which contains all the indexes that corresponds to the following request
def get_our_index(user_input, city):
    print(user_input)
    db = receive_database()
    cursor = db.index_data.find({"city": city})
    addresses_i_found = {}
    for document in cursor:
        address = str(document['address'])
        index = str(document["index"])
        if user_input.upper() in address.upper():
            addresses_i_found.update({address: index})
    return addresses_i_found


# Shall be used to generate the dynamic inline query
def receive_supported_cities():
    db = receive_database()
    cities_list = db.index_data.distinct("city")
    return cities_list
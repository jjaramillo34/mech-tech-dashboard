import hashlib
import pymongo
#import streamlit as st
import streamlit_authenticator as stauth
import datetime
from decouple import config

#@st.experimental_singleton
def init_connection():
    #return pymongo.MongoClient(**st.secrets["db_users"])
    mongoDB = pymongo.MongoClient(config('MONGO_URI'))
    return mongoDB

client = init_connection()

def insert_user(username, name, password, hashed_password, date_r, is_manager, is_superuser, is_staff, is_active, phone_number_assigned, location):
    db = client["db_users"]
    collection = db["mech_tech_users"]
    bracketPass = [password]
    hashed_password= stauth.Hasher(bracketPass).generate()
    strPass=str(hashed_password)
    removeopenbrack=strPass.replace("[", "")
    removeclosebrack=removeopenbrack.replace("]", "")
    final=removeclosebrack.replace("'","")
    date_r = datetime.datetime.now()
    collection.insert_one(
        {
            "username": username,
            'name': name,
            "string_password": password,
            "hash_password": final,
            "date_registered": date_r,
            "is_manager": is_manager,
            "is_superuser": is_superuser,
            "is_staff": is_staff,
            "is_active": is_active,
            'phone_number_assigned': phone_number_assigned,
            'location': location,
        }
    )
    return f"User added successfully {username}, {final}"

def update_password(username, password, hashed_password):
    db = client["db_users"]
    collection = db["mech_tech_users"]
    bracketPass = [password]
    hashed_password= stauth.Hasher(bracketPass).generate()
    strPass=str(hashed_password)
    removeopenbrack=strPass.replace("[", "")
    removeclosebrack=removeopenbrack.replace("]", "")
    final=removeclosebrack.replace("'","")
    collection.update_one({"username": username}, {"$set": {"hash_password": final, "string_password": password}})
    return f"Password updated successfully {username}, {final}"

def delete_user(username):
    db = client["db_users"]
    collection = db["mech_tech_users"]
    collection.delete_one({"username": username})
    return f"User deleted successfully {username}"

#@st.experimental_memo(ttl=60)
def update_user(username):
    db = client["db_users"]
    collection = db["mech_tech_users"]
    collection.update_one({"username": username})
    return f"User updated successfully {username}"

#@st.experimental_memo(ttl=60)
def fetch_all_users():
    db = client["db_users"]
    collection = db["mech_tech_users"]
    #return "select username, name, password, hash_password, date_registered, is_admin from mech_tech_users"
    return collection.find()

def insert_likes(username, text, likes, date_r):
    db = client["db_users"]
    collection = db["mech_tech_likes"]
    collection.insert_one(
        {
            "username": username,
            "text": text,
            "likes": likes,
            "date_liked": date_r,
        }
    )
    return f"Likes added successfully {username}, {likes}"

def insert_feedback(username, text, date_r, rating):
    db = client["db_users"]
    collection = db["mech_tech_feedback"]
    collection.insert_one(
        {
            "username": username,
            "text": text,
            "date_feedback": date_r,
            'rating': rating,
        }
    )
    return f"Feedback added successfully {username}, {text}"

def average_ratings():
    db = client["db_users"]
    collection = db["mech_tech_feedback"]
    x = collection.aggregate([
        {
            "$group": {
                "_id": None,
                "avg_rating": { "$avg": "$rating" }
            }
        }
    ])
    return list(x)[0]['avg_rating']

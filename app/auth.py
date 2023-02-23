import hashlib
import pymongo
import streamlit as st
import streamlit_authenticator as stauth
import datetime

st.set_page_config(
    page_title="Mech Tech Tools",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': 'mailto:javier@datanaly.st',
        'About': "Mech Tech Tools - Collection of tools built for the Mech Tech community."
    }
)

@st.experimental_singleton
def init_connection():
    return pymongo.MongoClient(**st.secrets["db_users"])

client = init_connection()

def insert_user(username, name, password, hashed_password, date_r, is_manager, is_superuser, is_staff, is_active, phone_number_assigned, location) :
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
            "password": password,
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


#insert_user("admin", "admin", "password", '$2b$12$rG1e2XkT1UcRRbFki5jzR.fpQiNoBETG1BSsXQZVTj/yijbzX1hgm', datetime.datetime.now(), False, True, False, True, '')


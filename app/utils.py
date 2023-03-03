import os
import pandas as pd
from datetime import datetime
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from decouple import config
import logging
import streamlit as st

logging.basicConfig(filename="logs.log",
                    filemode="a",
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%d-%b-%y %H:%M:%S",
                    level=logging.DEBUG)

TWILIO_ACCOUNT_SID = config("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = config("TWILIO_AUTH_TOKEN")
#TWILIO_NUMBER = config("TWILIO_NUMBER")
logger = logging.getLogger(__name__)
twilio_api = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def get_all_numbers():
    #phone_numbers = twilio_api.incoming_phone_numbers.list()
    # Get the list of phone numbers
    phone_numbers = twilio_api.incoming_phone_numbers.list()
    numbers = []
    # Loop through the phone numbers and print their friendly name and phone number
    for number in phone_numbers:
        print(f'Friendly Name: {number.friendly_name} Phone Number: {number.phone_number}')    
        numbers.append(f"{number.friendly_name} - {number.phone_number}")
    return numbers

def fetch_calls(from_number):
    data = []
    doc = {}
    calls = twilio_api.calls.stream(from_=from_number)
    for i in calls:
        doc['From'] = i.from_
        doc['To'] = i.to
        doc['Date'] = i.date_created
        doc['Status'] = i.status
        doc['Duration'] = i.duration
        doc['Price'] = i.price
        doc['Price Unit'] = i.price_unit
        data.append(doc)
    return data

def fetch_sms(from_number):
    data = []
    doc = {}
    sms = twilio_api.messages.stream(from_=from_number)
    for s in sms:
        doc['From'] = s.from_
        doc['To'] = s.to
        #doc['Body'] = s.body
        doc['Date'] = s.date_sent
        doc['Day'] = s.date_sent.strftime('%d')
        doc['Month'] = s.date_sent.strftime('%B')
        doc['Year'] = s.date_sent.strftime('%Y')
        doc['Date Created'] = s.date_created
        doc['Status'] = s.status
        #doc['Direction'] = s.direction
        doc['Price'] = s.price
        try:
            doc['Price1'] = float(s.price[1:])
        except Exception as e:
            doc['Price1'] = None
        doc['Price Unit'] = s.price_unit
        data.append(doc)
    #return sorted(data, key=lambda k: k['Date'], reverse=False)
    return pd.DataFrame(data)

def send_messages_bulk(to, body, from_):
    try:
        twilio_api.messages.create(
            to=to,
            from_=from_,
            body=body,
        )
        date_r = datetime.now().strftime("%b %d, %Y")
        st.success(f"El mensaje se envió al número {to} de parte {from_} el dia {date_r} ")
        logger.info("Message sent to {}".format(to))
    except TwilioRestException as e:
        logger.error(e)
        #st.error("Error sending message to {}: {}".format(to, e))
        st.error("Se ha producido un error al enviar el mensaje al número: {}".format(to) + " Por favor, verifique que el número sea correcto")
        

def send_messages_bulk_sms_with_media(to, body, from_, media_url):
    try:
        twilio_api.messages.create(
            to=to,
            from_=from_,
            body=body,
            media_url=[media_url],
        )
        date_r = datetime.now().strftime("%b %d, %Y")
        st.success(f"El mensaje se envió al número {to} de parte {from_} el dia {date_r} ")
        logger.info("Message sent to {}".format(to))
    except TwilioRestException as e:
        logger.error(e)
        #st.error("Error sending message to {}: {}".format(to, e))
        st.error("Se ha producido un error al enviar el mensaje al número: {}".format(to) + " Por favor, verifique que el número sea correcto")
        
def send_messages_bulk_with_video(to, body, from_, media_url):
    try:
        twilio_api.messages.create(
            to=to,
            from_=from_,
            body=body,
            media_url=[media_url],
        )
        st.success("Message sent to {}".format(to))
        logger.info("Message sent to {}".format(to))
    except TwilioRestException as e:
        logger.error(e)
        st.error("Error sending message to {}: {}".format(to, e))
            
def send_messages_bulk_whatsapp(to, body):
    try:
        twilio_api.messages.create(
            to=to,
            from_='whatsapp:+14155238886',
            body=body,
        )
        st.success("Message sent to {}".format(to))
        logger.info("Message sent to {}".format(to))
    except TwilioRestException as e:
        logger.error(e)
        st.error("Error sending message to {}: {}".format(to, e))
        
def send_messages_bulk_email(to, body):
    try:
        twilio_api.messages.create(
            to=to,
            from_='email',
            body=body,
        )
        st.success("Message sent to {}".format(to))
        logger.info("Message sent to {}".format(to))
    except TwilioRestException as e:
        logger.error(e)
        st.error("Error sending message to {}: {}".format(to, e))
        
def fetch_calls():
    return twilio_api.calls.stream()

def fethc_sms_by_account():
    return twilio_api.messages.stream(account_sid=TWILIO_ACCOUNT_SID)        

#def fetch_sms_by_number():
#    return twilio_api.messages.stream(from_=TWILIO_NUMBER)

def version():
    return st.sidebar.caption(f"Stremalit Version: {st.__version__}")


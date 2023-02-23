import random
import time
import openai
import requests
import re
import base64
import toml
from urllib import request
from datetime import datetime
import streamlit as st
import pandas as pd
from io import BytesIO
from decouple import config
from streamlit_option_menu import option_menu
from streamlit_text_rating.st_text_rater import st_text_rater
#from annotated_text import annotated_text
from PIL import Image
from bs4 import BeautifulSoup
from utils import fetch_calls, send_messages_bulk, get_all_numbers, fetch_sms, send_messages_bulk_sms_with_media
from auth import fetch_all_users, insert_likes, insert_user
from streamlit_ace import st_ace
from streamlit_quill import st_quill
import streamlit_authenticator as stauth  # pip install streamlit-authenticator
from streamlit_player import st_player
from streamlit_chat import message
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
#from auth import login_page, signup_page

#st.set_page_config(page_title="Streamlit Option Menu", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
# get all users from db
users = fetch_all_users()

usernames, names, passwords, managers, superusers, staffers, activeusers, phones = [], [], [], [], [], [], [], []

for user in users:
    usernames.append(user["username"])
    names.append(user["name"])
    passwords.append(user["hash_password"])
    managers.append(user["is_manager"])
    superusers.append(user["is_superuser"])
    staffers.append(user["is_staff"])
    activeusers.append(user["is_active"])
    phones.append(user["phone_number_assigned"])

cred = {"usernames":{}} # create empty dict

for uname, name, pwd, manager, superuser, staff, activeuser, phone in zip(usernames, names, passwords, managers, superusers, staffers, activeusers, phones):
    user_dict = {"name":name, "password":pwd, "is_manager": manager, "is_superuser": superuser, "is_staff": staff, "is_active": activeuser, "phone_number_assigned": phone}
    #print(user_dcit)
    cred["usernames"].update({uname:user_dict})
    
#st.write(cred)
authenticator = stauth.Authenticate(cred, "sales_dashboard", "abcdef", cookie_expiry_days=30)

name, authentication_status, username = authenticator.login('Login', 'main')

# regex patterns for email and phone numbers (could be simpler if more basic matching is required)
email_regex_pattern = r'(?:[a-z0-9!#$%&''*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&''*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])'
phone_number_regex_pattern = r'(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?'

@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

@st.cache
def convert_to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'}) 
    worksheet.set_column('A:A', None, format1)  
    writer.save()
    processed_data = output.getvalue()
    return processed_data

def st_display_pdf(pdf_file, height=None):
    with open(pdf_file, 'rb') as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height={height} type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

primaryColor = toml.load(".streamlit/config.toml")['theme']['primaryColor']
s = f"""
<style>
div.stButton > button:first-child {{ border: 5px solid {primaryColor}; border-radius:20px 20px 20px 20px; }}
<style>
"""

st.markdown(s, unsafe_allow_html=True)

def generate_response(prompt):
    try:
        completions = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=0.9,
            max_tokens=1024,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.6,
            stop=[" Human:", " AI:"]
        )
        message = completions.choices[0].text
        return message
    except Exception as e:
        print(e)
        return "Error"

# We will get the user's input by calling the get_text function
def get_text():
    input_text = st.text_input("You: ","Necesito información sobre mech-tech college en puerto rico", key="input")
    return input_text

def get_text(text):
    input_text = st.text_input("You: ",text, key="input")
    return input_text

def show_pdf(file_path):
    with open(file_path,"rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="800" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)
    
def find_phone_number(text):
    ph_no = re.findall(r"\b\d{11}\b",text)
    print(ph_no)
    if len(ph_no) > 0:
        return True
    else:
        return False
    
def get_users_data():
    users = fetch_all_users()    
    doc_users = {}
    data_user = []
    for user in users:
        doc_users.update({
            'username': user['username'],
            'name': user['name'],
            'phone': user['phone_number_assigned'],
            'location': user['location'],
            'is_manager': user['is_manager'],
            'is_staff': user['is_staff'],
            'is_superuser': user['is_superuser'],
            'is_active': user['is_active'],
            'date_joined': user['date_registered'],
            })
        data_user.append(doc_users)
        doc_users = {}
        #print(doc_users)
    df = pd.DataFrame(data_user)
    return df
        
            
def home():
    
    display = "https://www.mtifl.com/wp-content/uploads/2015/06/logo.png"
    col1, col2, col3 = st.columns([1,6,1])

    with col1:
        st.write("")

    with col2:
        #st.image("https://i.imgflip.com/amucx.jpg")
        st.image(display)

    with col3:
        st.write("")
    
    #col2.title("Mech Tech International Tools")
    st.markdown("<h1 style='text-align: center; color: white;'>Mech Tech Institute Tools</h1>", unsafe_allow_html=True)
    st.write("")
    cols = st.columns([7, 3])
    with cols[0]:
        st.image('https://www.mtifl.com/wp-content/uploads/2015/06/Racing-Mechanics.jpg', use_column_width=True)
    with cols[1]:
        st.subheader("Mech-Tech College")
        st.write("")
        st.write("""
                 Mech-Tech is a for-profit college located in Caguas, Puerto Rico in the San Juan Area. It is a small institution with an enrollment of 1,777 undergraduate students. The Mech-Tech acceptance rate is 100%. Popular majors include Automotive Mechanics, 
                 Welding, and Mechanics and Repair. Graduating 59% of students, Mech-Tech alumni go on to earn a starting salary of $16,700.
                 """)
        st.write("")
        
def dashboard():
    
    st.markdown("""
<style>
div[data-testid="metric-container"] {
   background-color: rgba(28, 131, 225, 0.1);
   border: 1px solid rgba(28, 131, 225, 0.1);
   padding: 5% 5% 5% 10%;
   border-radius: 5px;
   color: rgb(30, 103, 119);
   overflow-wrap: break-word;
}

/* breakline for metric text         */
div[data-testid="metric-container"] > label[data-testid="stMetricLabel"] > div {
   overflow-wrap: break-word;
   white-space: break-spaces;
   color: red;
}
</style>
"""
, unsafe_allow_html=True)
    
    call_sms = st.sidebar.radio("Select Option", ["Calls", "SMS"])
    
    if call_sms == "Calls":    
        # Get the recipient phone numbers
        st.title('Calls By Number')
        #st.st_magic("reload_ext autoreload")
        direction, date_created, date_sent, error_code, error_message, from_, to, status, price, price_unit = [], [], [], [], [], [], [], [], [], []
        
        sms = fetch_calls()
        for x in sms:
            direction.append(x.direction)
            date_created.append(x.date_created)
            #date_sent.append(x.date_sent)
            #error_code.append(x.error_code)
            #error_message.append(x.error_message)
            from_.append(x.from_)
            to.append(x.to)
            status.append(x.status)
            if x.price is not None:
                price.append(float(x.price))
            else:
                price.append(x.price)
                
            price_unit.append(x.price_unit)
            
        #print(direction)
        df = pd.DataFrame({
            'Direction': direction,
            'Date Created': date_created,
            #'Date Sent': date_sent,
            #'Error Code': error_code,
            #'Error Message': error_message,
            'From': from_,
            'Price': price,
            'Price Unit': price_unit,
            'Status': status,
            'To': to,
        })
        
        df = df.dropna(subset=['Price'], axis=0).reset_index(drop=True)
        #st.dataframe(df, use_container_width=True)
        
        df_to = df['To'].unique()
        df_to = sorted(df_to)
        to_numbers = st.sidebar.multiselect("Filter By Number:", df_to)
            
        if to_numbers in df_to:
            #st.write("All")
            df = df.query("To in @to_numbers")
            st.dataframe(df, use_container_width=True)
            st.write("Data Dimension: " + str(df.shape[0]) + " rows and " + str(df.shape[1]) + " columns.")
    elif call_sms == 'SMS':
        numbers = get_all_numbers()
        from_number = st.sidebar.selectbox("Select the list of numbers to send the message:", numbers)
        from_ = from_number.split('-')[1].strip()
        sms_logs = fetch_sms(from_)
        
        st.title('SMS Logs')
        
        cols = st.columns(3)
        cols[0].metric("Total SMS Sent", sms_logs.shape[0])
        cols[1].metric("Total SMS Delivered", sms_logs[sms_logs['Status'] == 'delivered'].shape[0])
        cols[2].metric("Total SMS Failed", sms_logs[sms_logs['Status'] == 'failed'].shape[0])
        
        cols = st.columns(3)
        cols[0].metric("Total SMS Queued", sms_logs[sms_logs['Status'] == 'queued'].shape[0])
        cols[1].metric("Total Spend", round(sms_logs['Price1'].sum(), 4))
        cols[2].metric("Total SMS Sent", round(sms_logs['Price1'].sum(), 4))
        st.dataframe(sms_logs.head(10), use_container_width=True)
        st.write("Data Dimension: " + str(sms_logs.shape[0]) + " rows and " + str(sms_logs.shape[1]) + " columns.")
        
        st.date_input("Select Date Range", [sms_logs['Date Created'].min(), sms_logs['Date Created'].max()])
        
def tools():
    #st.write(cred)
    menu_options = ['Bulk SMS', 'Bulk Email', 'Bulk Whatsapp', 'Bulk Telegram']
    menu_icons = ['phone', 'email', 'whatsapp', 'telegram']
    
    #st.sidebar.image(display, width=200)
    selected2 = option_menu(None, menu_options, 
        icons=menu_icons, menu_icon="cast", default_index=0, orientation="horizontal")
    
    if selected2 == "Bulk SMS":
        # media type options
        media_type_options = {"image": "media", "video": "video", "audio": "audio", "document": "document"}
        from_ = phone
        
        st.sidebar.info('Numero de origen: ' + phone)
        type_of_input = st.sidebar.radio('Select the type of input', ['From Input Form', 'From CSV File'])
        st.sidebar.write("---")
        
        df_sample_csv = pd.read_csv('files/cms_bulk.csv')
        df_sample_excel = pd.read_excel('files/cms_bulk.xlsx')
        download_sample_csv = convert_df(df_sample_csv)
        download_sample_excel = convert_to_excel(df_sample_excel)
        
        media_allowed = st.sidebar.checkbox(label='Allow media in message: ', value=False)
        columns_name_allow = [x.lower() for x in ['Phone Number', 'CellPhone', 'Cell_Phone', 'Cell-Phone', 'Cell_Phone', 'Cell', 'Celular', 'Telefono', 'Phone']]
                
        if media_allowed:
            media_type = st.sidebar.selectbox('Allow media in message: ', ['image', 'video', 'audio'])
            if type_of_input == 'From Input Form':
                media_url = st.text_input(f"Enter the {media_type_options[media_type]} url:")
                recipients = st.text_area("Enter the recipient phone numbers (one per line):", height=200)
                recipients = recipients.strip().split("\n")

                # Get the message to send
                message = st.text_area("Por favor, ingrese el mensaje a enviar:", height=200)
                
                if st.button("Send"):
                    for recipient in recipients:
                        time.sleep(2)
                        send_messages_bulk_sms_with_media(recipient, message, from_, media_url)
            
            elif type_of_input == 'From CSV File':
                st.info('Por favor, asegurese de que el nombre de la columna contenga uno de los siguientes nombres: {}'.format(columns_name_allow))
                cols = st.columns(2)
                cols[0].download_button("Descargar archivo de muestra csv", download_sample_csv, 'sample.csv', 'text/csv')
                cols[1].download_button("Descargar archivo de muestra excel", download_sample_excel, 'sample.xlsx')
                file = st.file_uploader("Choose a CSV or XLSX file", type=["csv", "xlsx"])
                if file is not None:
                    try:
                        df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
                        df.columns = df.columns.str.lower()
                        for col_name in columns_name_allow:
                            if col_name in df.columns:
                                df = df.rename(columns={col_name: 'phonenumber'})
                                break
                        columns = [col for col in df.columns]
                        df['phonenumber'] = df['phonenumber'].astype(str)
                        #st.write(columns)
                        
                        df['verified'] = df[columns].apply(lambda x: x.str.contains(phone_number_regex_pattern,regex=True)).any(axis=1)
                        df['verified1'] = df[columns].apply(lambda x: x.str.contains(phone_number_regex_pattern,regex=True)).any(axis=1)
                        
                        if df['verified'].all():
                            st.success('El archivo no tiene errores')
                        else:
                            st.error('Por favor, chequee la fila: {}'.format(df[df['verified'] == False].index.tolist()) + ' y asegurese de que la columna de telefonos contenga solo numeros en la forma: 14141234567')
                        
                        df['phonenumber'] = df['phonenumber'].astype(str)
                        
                        st.dataframe(df, use_container_width=True)
                        
                        mensaje = f"Hola {df['name'][0]}, {df['notas'][0]}"        
                        recipients1 = [(df['phonenumber'][i], df['name'][i], df['notas'][i]) for i in range(len(df))]
                        
                        used_notas = st.checkbox(label='Utilice la columna de notas: ', value=False)
                        
                        media_url = st.text_input(f"Enter the {media_type_options[media_type]} url:")
                        
                        if used_notas == False:
                            message = st.text_area("Enter the message to send:", placeholder=mensaje, key='message')
                        else:
                            message = st.text_area("Enter the message to send:", key='message', disabled=True)
                        
                        mensaje = message
                        
                        if st.button("Send", help="Enviar mensajes"):
                            if used_notas:
                                for i, recipient in enumerate(recipients1):
                                    #print(recipient[i])
                                    message = f"Hola {recipient[1]}, {recipient[2]}"
                                    time.sleep(2)
                                    send_messages_bulk(recipient[0], message, from_)
                            else:
                                for i, recipient in enumerate(recipients1):
                                    #print(recipient[i])
                                    time.sleep(2)
                                    send_messages_bulk(recipient[0], message, from_)
                    except Exception as e:
                        st.error(e)
        
        else:
            if type_of_input == 'From Input Form':
                recipients = st.text_area("Enter the recipient phone numbers (one per line):", height=200)
                recipients = recipients.strip().split("\n")

                # Get the message to send
                message = st.text_area("Enter the message to send:")
                
                if st.button("Send"):
                    for recipient in recipients:
                        time.sleep(2)
                        send_messages_bulk(recipient, message, from_)
            
            elif type_of_input == 'From CSV File':
                st.info('Por favor, asegurese de que el nombre de la columna contenga uno de los siguientes nombres: {}'.format(columns_name_allow))
                cols = st.columns(2)
                cols[0].download_button("Descargar archivo de muestra csv", download_sample_csv, 'sample.csv', 'text/csv')
                cols[1].download_button("Descargar archivo de muestra excel", download_sample_excel, 'sample.xlsx')
                file = st.file_uploader("Choose a CSV or XLSX file", type=["csv", "xlsx"])
                if file is not None:
                    try:
                        df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
                        df.columns = df.columns.str.lower()
                        for col_name in columns_name_allow:
                            if col_name in df.columns:
                                df = df.rename(columns={col_name: 'phonenumber'})
                                break
                        columns = [col for col in df.columns]
                        df['phonenumber'] = df['phonenumber'].astype(str)
                        
                        #df['verified'] = df[columns].apply(lambda x: x.str.contains(phone_number_regex_pattern,regex=True)).any(axis=1)
                        df['verified']=df['phonenumber'].apply(lambda x: find_phone_number(x))
                        
                        if df['verified'].all():
                            st.success('El archivo no tiene errores')
                            no_errors = df[df['verified'] == True].index.tolist()
                            gb = GridOptionsBuilder.from_dataframe(df)
                            gb.configure_selection('multiple', pre_selected_rows=no_errors)
                            response = AgGrid(
                                df,
                                editable=False,
                                gridOptions=gb.build(),
                                data_return_mode="filtered_and_sorted",
                                update_mode="no_update",
                                fit_columns_on_grid_load=True,
                                theme='balham',
                            )
                        else:
                            st.error('Por favor, chequee la fila: {}'.format(df[df['verified'] == False].index.tolist()) + ' y asegurese de que la columna de telefonos contenga solo numeros en la forma: 14141234567')
                            rows_errors = df[df['verified'] == False].index.tolist()                        
                            gb = GridOptionsBuilder.from_dataframe(df)
                            gb.configure_selection('multiple', pre_selected_rows=rows_errors)
                            response = AgGrid(
                                df,
                                editable=False,
                                gridOptions=gb.build(),
                                data_return_mode="filtered_and_sorted",
                                update_mode="no_update",
                                fit_columns_on_grid_load=True,
                                theme='streamlit',
                            )
                        df['phonenumber'] = df['phonenumber'].astype(str)
                    
                        mensaje = f"Hola {df['name'][0]}, {df['notas'][0]}"
                        mensaje_placeholder = "{greetings}, {name} {notas}".format(greetings='Buenos dias', name=df['name'][0], notas=df['notas'][0])
                        st.write(mensaje_placeholder)
                        
                        recipients = df['phonenumber'].tolist()
                        
                        recipients1 = [(df['phonenumber'][i], df['name'][i], df['notas'][i]) for i in range(len(df))]
                        
                        used_notas = st.checkbox(label='Utilice la columna de notas: ', value=False)
                        
                        if used_notas == False:
                            message = st.text_area("Enter the message to send:", placeholder=mensaje, key='message')
                        else:
                            message = st.text_area("Enter the message to send:", key='message', disabled=True)
                        
                        mensaje = message
                        if st.button("Send", help="Enviar mensajes"):
                            if used_notas:
                                for i, recipient in enumerate(recipients1):
                                    #print(recipient[i])
                                    message = f"Hole {recipient[1]}, {recipient[2]}"
                                    time.sleep(2)
                                    send_messages_bulk(recipient[0], message, from_)
                                    
                            else:
                                for i, recipient in enumerate(recipients1):
                                    if mensaje == '':
                                        st.error('El mensaje no puede estar vacio')
                                    else:
                                        time.sleep(2)
                                        send_messages_bulk(recipient[0], message, from_)
                    except Exception as e:
                        st.error(e)
                        
    elif selected2 == "Bulk Email":
        st.write("Bulk Email")
        st.write("Coming Soon")
    
    elif selected2 == "Bulk Whatsapp":
        st.write("Bulk Whatsapp")
        st.write("Coming Soon")
        
def chatbot():
    
    preguntas =[
                "¿Qué es Mech-Tech College?",
                "¿Qué programas ofrece Mech-Tech College?",
                "¿Qué tipo de certificados ofrece Mech-Tech College?",
                "¿Qué tipo de cursos ofrece Mech-Tech College?",
                "Necesito ayuda acerca de los programas de Mech-Tech College", 
                "¿Cómo puedo inscribirme a Mech-Tech College?",
                "¿Cómo puedo inscribirme a un curso de Mech-Tech College?",
                "¿Cómo puedo pagar a Mech-Tech College?", 
                "¿Cómo puedo obtener mi certificado a Mech-Tech College?",
                "¿Cómo puedo obtener mi diploma a Mech-Tech College?",
                "¿Cómo puedo obtener mi certificado de asistencia a Mech-Tech College?",
                "¿Cómo puedo obtener mi certificado de participación a Mech-Tech College?",
                "Quiero saber más acerca de los cursos de Mech-Tech College",
                "Quiero saber más acerca de los programas de Mech-Tech College",
                "Quiero contactarme con la persona encargada de los programas de Mech-Tech College",
                'Cual es el mensaje del presidente de Mech-Tech College para los estudiantes',
                '¿Qué Programas Ofrecemos en nuestro Recinto de Mayagüez?',
                ]
    
    random_index_pregunta = random.randint(0, len(preguntas)-1)
    
    initial_text = st.sidebar.selectbox("Que preguntas quieres hacerle a Mech-Tech AIChatBox", preguntas, index=random_index_pregunta)
    
    st.title("Preguntas frecuentes, Mech-Tech AIChatBox tiene la respuesta")
    openai.api_key = config("OPENAI_API_KEY")
        # Storing the chat
    if 'generated' not in st.session_state:
        st.session_state['generated'] = []

    if 'past' not in st.session_state:
        st.session_state['past'] = []
    
    user_input = get_text(initial_text)

    if user_input:
        with st.spinner("MecheTeche AIChatBox esta pensado por favor espere ..."):
            output = generate_response(user_input)
            # store the output 
            st.session_state.past.append(user_input)
            st.session_state.generated.append(output)
        
    if st.session_state['generated']:
        for i in range(len(st.session_state['generated'])-1, -1, -1):
            message(st.session_state["generated"][i], key=str(i))
            message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')
            
    #clear the chat
    if st.sidebar.button("Clear Chat"):
        # reset the session state
        st.session_state.generated = []
        st.session_state.past = []
        output = None
            
def about():
    cols = st.columns((6, 4))
    with cols[0]:
        #st.subheader("Login Page Admin Login View and User Login View")
        parameters={"controls": 1, "autoplay": 0, "loop": 1, "muted": 1, "rel": 0, "modestbranding": 1, "playsinline": 1, "origin": "https://share.streamlit.io", "widgetid": 1}
        
        st_player("https://youtu.be/YgizIT3jRLk", height=500, controls=True, loop=True)
        #st.video("videos/login.webm")
        #st.image("videos/login.gif", use_column_width=True)
    with cols[1]:
        #st.subheader("Admin Dashboard")
        st.markdown(""" <style> .font {
            font-size:22px ; font-family: 'Black'; color: #FFFFF;} 
            </style>""", unsafe_allow_html=True)
        st.markdown('<p class="font">Mech Tech User or Admin Login Views</p>', unsafe_allow_html=True)
        st.markdown(""" <style> .font {
            font-size:15px ; font-family: 'Black'; color: #FFFFF;}
            </style>""", unsafe_allow_html=True)    
        st.markdown("""
                    - En esta sección se puede ver el inicio de sesión de la página de administración y la página de inicio de sesión de usuario.
                    - En la página de inicio de sesión de usuario, el usuario puede iniciar sesión con su nombre de usuario y contraseña.
                    - En la página de inicio de sesión de administrador, el administrador puede iniciar sesión con su nombre de usuario y contraseña.
                    - Si el usario ingresado es incorrecto, se mostrará un mensaje de error.
                    - Si el usuario ingresado es correcto, se mostrará la página de inicio de sesión de usuario.
                    - Si el administrador ingresado es incorrecto, se mostrará un mensaje de error.
                    - Si el administrador ingresado es correcto, se mostrará la página de inicio de sesión de administrador.
                    - Si el usuario o el administrador olvida su contraseña, puede restablecerla.
                    """)
    col1, col2,col3= st.columns(3)
    with col1:
        with open("pdf/login.pdf", "rb") as pdf_file:
            PDFbyte = pdf_file.read()
        st.download_button(label="Download PDF Tutorial", key='3.4',
                data=PDFbyte,
                file_name="pdf/login.pdf",
                mime='application/octet-stream')

    for text in ["Te parecio util este tutorial?"]:
        date_r = datetime.now()
        response = st_text_rater(text=text, key='likes1.4')
        if response is not None:
            insert_likes(name ,text, response, date_r)
        #st.write(response)

if __name__ == "__main__":
    if authentication_status == False:
        st.error("Usario o contraseña incorrectos")

    if authentication_status == None:
        st.warning("Por favor, ingrese su usuario y contraseña")
        
    if authentication_status == True and cred['usernames'][username]['is_manager'] == True:
        #placeholder = st.empty()
    
        authenticator.logout('Cerrar Sesión', 'sidebar')
        st.sidebar.markdown(f'<p style="color: #ff4b4b; font-size: 16px; font-family: "Black";">Logged in as: {name}</p>', unsafe_allow_html=True)
        #st.sidebar.markdown(f'<div class="alert alert-primary" role="alert"> This is a primary alert—check it out!</div>', unsafe_allow_html=True)
        #st.sidebar.write(f'Logged is as: {name}')
        
        #with st.sidebar:
        #    annotated_text("Logged in as: ", (f"{name}", "#faa"))
        #st.set_page_config(page_title="Streamlit Option Menu", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
        menu_options = ['Inicio', 'Panel', 'Herramientas', 'Configuración', 'Preguntas', 'Ayuda']
        menu_icons = ['house', 'cast', 'tools', 'gear', 'question', 'info']
        # 1. as sidebar menu
        with st.sidebar:
            selected = option_menu("Menú principal", menu_options, 
                icons=menu_icons, menu_icon="list", default_index=0)
        
        if selected == "Inicio":
            #st.write(get_username())
            home()
        elif selected == "Panel":
            dashboard()
        elif selected == "Herramientas":
            tools()
        elif selected == "Configuración":
            st.title("Configuración")
            st.write("Bienvenido a la sección de configuración")
        elif selected == "Preguntas":
            chatbot()
        elif selected == "Ayuda":
            about()
            st.write('---')
        display = "https://www.mtifl.com/wp-content/uploads/2015/06/logo.png"
        st.sidebar.image(display, width=200)
        
        st.sidebar.caption("Developed by Javier Jaramillo")
        with st.sidebar.expander("Version 1.0.0.0"):
            #st.write("Version 1.0.0")
            for text in ["Is this text helpful?", "Do you like this text?"]:
                response = st_text_rater(text=text)
                st.write(f"response --> {response}")
    
    elif authentication_status == True and cred['usernames'][username]['is_staff'] == True:
        authenticator.logout('Cerrar sesión', 'sidebar')
        st.sidebar.write(f'Bienvenido {name}')
        menu_options = ['Inicio', 'Herramientas', 'Ayuda']
        menu_icons = ['house', 'tools', 'info']
        with st.sidebar:
            selected = option_menu("Menú principal", menu_options, 
                icons=menu_icons, menu_icon="list", default_index=0)
        if selected == "Inicio":
            home()
        elif selected == "Herramientas":
            tools()
        elif selected == "Ayuda":
            about()
            st.write('---')
        display = "https://www.mtifl.com/wp-content/uploads/2015/06/logo.png"
        st.sidebar.image(display, width=200)
        st.sidebar.caption("Programmed by Javier Jaramillo:")
        with st.sidebar.expander("Version"):
            st.write("Version 1.0.0")
            for text in ["Is this text helpful?", "Do you like this text?"]:
                response = st_text_rater(text=text)
                st.write(f"response --> {response}")
    
    if authentication_status == True and cred['usernames'][username]['is_superuser'] == True:
        st.sidebar.image('https://www.mtifl.com/wp-content/uploads/2015/06/logo.png', width=200)
        authenticator.logout('Cerrar sesión', 'sidebar')
        st.sidebar.write(f'Bienvenido {name}')
        st.sidebar.write('---')
        select_box = st.sidebar.selectbox('Seleccione una opción', ['Crear usuario', 'Eliminar usuario', 'Editar usuario', 'Ver todos los usuarios'])
        
        phone_numbers = get_all_numbers()
        
        users = fetch_all_users()
        
        doc_users = {}
        data_user = []
        for user in users:
            #print(user)
            doc_users.update({
                'username': user['username'],
                'name': user['name'],
                'phone': user['phone_number_assigned'],
                'location': user['location'],
                'is_manager': user['is_manager'],
                'is_staff': user['is_staff'],
                'is_superuser': user['is_superuser'],
                'is_active': user['is_active'],
                'date_joined': user['date_registered'],
                })
            
            data_user.append(doc_users)
            doc_users = {}
            print(doc_users)
            
        df = pd.DataFrame(data_user)
        
        #st.write(phones)
        cols = st.columns(2)
        
        if select_box == 'Crear usuario':
            with st.form(key='my_form'):
                uname = st.text_input('Nombre de usuario', placeholder='Ingrese el nombre de usuario', max_chars=20, help='Ingrese el nombre de usuario')
                name = st.text_input('Nombre - Apellido', placeholder='Ingrese el Nombre y Apellido del usuario', max_chars=40, help='Ingrese el nombre del usuario')
                password = st.text_input('Contraseña', type='password', placeholder='Ingrese la contraseña del usuario', max_chars=20, help='Ingrese la contraseña del usuario')
                phone = st.selectbox('Seleccione el número de teléfono que quiere a', phone_numbers, help='Seleccione el número de teléfono que quiere asignar al usuario')
                is_manager = st.checkbox('Es manager', value=False, key=None, help='Seleccione si el usuario es manager')
                is_staff = st.checkbox('Es staff', value=False, key=None, help='Seleccione si el usuario es staff')
                is_superuser = st.checkbox('Es superusuario', value=False, key=None, help='Seleccione si el usuario es superusuario', disabled=True)
                is_active = st.checkbox('Es activo', value=True, key=None, help='Seleccione si el usuario es activo')
                date_r = datetime.now()
                
                submit_button = st.form_submit_button(label='Crear usuario', help='Crear usuario')
                if submit_button:
                    time.sleep(2)
                    insert_user(uname, name, password, password, date_r, is_manager, is_superuser, is_staff, is_active, phone.split('-')[1], phone.split('-')[0])
                    st.balloons()
                    st.success('Usuario creado exitosamente.... ')
                    
                    st.write('---')
                    #st.write(respose)
                
        elif select_box == 'Eliminar usuario':
            #remover_user = st.selectbox('Seleccione el usuario que desea eliminar', df['username'])
            #if st.button('Eliminar usuario'):
            #    time.sleep(2)
                #delete_user(remover_user)
            #    st.balloons()
            #    st.success('Usuario eliminado exitosamente.... ')
                

            with st.form("my_form"):
                st.write("Inside the form")
                slider_val = st.slider("Form slider")
                checkbox_val = st.checkbox("Form checkbox")

                # Every form must have a submit button.
                submitted = st.form_submit_button("Submit")
                if submitted:
                    st.write("slider", slider_val, "checkbox", checkbox_val)

            st.write("Outside the form")
        
        elif select_box == 'Ver todos los usuarios':
            #AgGrid(df, 
            #       fit_columns_on_grid_load=False, 
            #       theme='streamlit', )
            st.title("Lista de usuarios")
            st.write('---')
            st.dataframe(df, use_container_width=True)
        
    else:
        pass
        #st.sidebar.image('https://www.mtifl.com/wp-content/uploads/2015/06/logo.png', width=200)
        #st.sidebar.write('---')
        #st.sidebar.write('Por favor, ingrese su usuario y contraseña')
        #st.sidebar.write('Por favor ingrese los datos solicitados')
        #st.sidebar.write('---')
        #placeholder = st.empty()
        #placeholder.info("CREDENTIALS ARE CASE SENSITIVE | username: admin | password: admin")
        #register = st.sidebar.button('Register')
        #if register:
        #    try:
        #        if authenticator.register_user('Register user'):
        #            st.success('User registered successfully')
        #    except Exception as e:
        #        st.error(e)
    
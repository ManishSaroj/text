import streamlit as st
import pyrebase  
import requests.exceptions
import os
import requests
import creds
from pydub import AudioSegment
import io
from time import sleep


# Initialize Firebase configuration
firebaseConfig = creds.firebaseConfig

firebase = pyrebase.initialize_app(firebaseConfig)

# Get Firebase Authentication instance
auth = firebase.auth()

# Define Streamlit app functions
def register():
    st.header("Create an account")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    if st.button("Register"):
        if password == confirm_password:
            try:
                # Create user account and login
                user = auth.create_user_with_email_and_password(email, password)
                # Send email verification
                auth.send_email_verification(user['idToken'])
                # Show success message and redirect to login page
                st.success("Account created! Please check your email to verify your account.")
            except:
                st.error("Registration failed!")
        else:
            st.error("Passwords do not match!")


def login():
    st.header("Login to your account")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        try:
            # Authenticate user with email and password
            user = auth.sign_in_with_email_and_password(email, password)
            
            # Check if email is verified
            user_info = auth.get_account_info(user['idToken'])['users'][0]
            email_verified = user_info['emailVerified']
            
            if email_verified:
                # Set session state to indicate successful login
                st.session_state.logged_in = True
            else:
                st.error("Please verify your email before logging in.")
                
        except requests.exceptions.HTTPError:
            st.error("Incorrect email or password. Please try again.")
        except:
            st.error("Authentication failed!")


def main_page():
    st.header("Welcome to the main page!")
    st.write("This is the main page of your app.")    
    # Add your Streamlit app content here
    # AssemblyAI API endpoint URLs
    upload_url = "https://api.assemblyai.com/v2/upload"
    transcript_url = "https://api.assemblyai.com/v2/transcript"

    # AssemblyAI API key
    API_KEY = creds.API_KEY

    # Streamlit app
    st.title("Audio Transcription with Textin")

    language = st.selectbox("Select language", ["Hindi", "English", "Spanish"])
    language_map = {
        "Hindi": "hi",
        "English": "en",
        "Spanish": "es"
    }

    # Upload file widget
    file = st.file_uploader("Choose an audio file", type=["mp3", "wav"])


    # Check if a file was uploaded
    if file is not None:
        # Preview the audio file
        audio_bytes = file.read()
        st.audio(audio_bytes, format='audio/wav')

        headers = {
            "authorization": API_KEY,
            "content-type": "application/json"
        }

        bar = st.progress(0)
    
        upload_response = requests.post(
            upload_url,
            headers=headers,
            data=audio_bytes
        )
        audio_url = upload_response.json()["upload_url"]
        st.info('Audio file has been uploaded to Textin')
        bar.progress(30)

        # Create transcription request
        json = {
            "audio_url": audio_url,
            "content_safety" : True,        
            "language_code" : language_map[language],
        
        }

        # Submit transcription request to AssemblyAI
        response = requests.post(
            transcript_url,
            headers=headers,
            json=json
        )

        st.info('Transcribing uploaded file')
        bar.progress(40)

        # Extract transcript ID
        transcript_id = response.json()["id"]
        st.info('Extract transcript ID')
        bar.progress(50)

        # Retrieve transcription results
        endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
        headers = {
            "authorization": API_KEY,
        }
        transcript_output_response = requests.get(endpoint, headers=headers)
        st.info('Retrieve transcription results')
        bar.progress(60)

        # Check if transcription is complete
        st.warning('Transcription is processing ...')
        while transcript_output_response.json()['status'] != 'completed':
            sleep(1)
            transcript_output_response = requests.get(endpoint, headers=headers)
        
        bar.progress(100)

        # Print transcribed text
        st.header('Output')
        
        with st.expander('Show Text'):
            st.success(transcript_output_response.json()["text"])


        

        # 9. Write JSON to app
        with st.expander('Show Full Results'):
            st.write(transcript_output_response.json())
        
        # 10. Write content_safety_labels
        with st.expander('Show content_safety_labels'):
            st.write(transcript_output_response.json()["content_safety_labels"])
        
        with st.expander('Summary of content_safety_labels'):
            st.write(transcript_output_response.json()["content_safety_labels"]["summary"])
            
    





# Define Streamlit app layout
st.set_page_config(page_title="My Streamlit App", page_icon=":rocket:")
st.title("My Streamlit App")

# Check if user is logged in
if not hasattr(st.session_state, "logged_in") or not st.session_state.logged_in:
    # Add container to hold login/register form
    with st.container():
        # Add radio button to select login or registration
        option = st.radio("Select an option", ("Login", "Register"), index=0)

        # Show login or registration form based on radio button selection
        if option == "Login":
            login()
        else:
            register()
else:
    main_page()
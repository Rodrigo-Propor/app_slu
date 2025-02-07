import streamlit as st
import pandas as pd
import hashlib
import datetime

# In-memory data storage (REPLACE WITH A DATABASE IN PRODUCTION)
users = {}
groups = {"users": [], "employees": [], "administrators": []}
admin_password = hashlib.sha256("admin".encode()).hexdigest() #Example - NEVER hardcode passwords


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login():
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        hashed_password = hash_password(password)
        if email in users and users[email]["password"] == hashed_password:
            st.session_state["logged_in"] = True
            st.session_state["user_email"] = email
            st.success("Logged in successfully!")
            st.experimental_rerun() #Refresh to show appropriate content
        else:
            st.error("Incorrect email or password.")

def signup():
    st.subheader("Sign Up")
    name = st.text_input("Name", key="signup_name")
    email = st.text_input("Email", key="signup_email")
    phone = st.text_input("Phone Number", key="signup_phone")
    dob = st.date_input("Date of Birth", key="signup_dob")
    password = st.text_input("Password", type="password", key="signup_password")
    if st.button("Sign Up"):
        if not name or not email or not password:
            st.error("Name, Email, and Password are required.")
        else:
            hashed_password = hash_password(password)
            users[email] = {"name": name, "phone": phone, "dob": dob, "password": hashed_password, "group": "users", "active": True}
            st.success("User created successfully!")
            st.experimental_rerun()


def forgot_password():
    st.subheader("Forgot Password")
    email = st.text_input("Email")
    if st.button("Reset Password"): #In reality, send a reset link via email
        if email in users:
            st.success("Password reset instructions sent to your email. (Simulated)") #Replace with actual email functionality
        else:
            st.error("Email not found.")


def admin_panel():
    if st.session_state["user_email"] in users and users[st.session_state["user_email"]]["group"] == "administrators":
        st.subheader("Admin Panel")
        df = pd.DataFrame.from_dict(users, orient='index')
        st.dataframe(df)

        #Simulate user management (replace with database interaction in production)
        selected_user = st.selectbox("Select User", list(users.keys()))
        if selected_user:
            user_data = users[selected_user]
            user_data["active"] = st.checkbox("Active", value=user_data["active"])
            user_data["group"] = st.selectbox("Group", ["users", "employees", "administrators"], index=["users", "employees", "administrators"].index(user_data["group"]))
            users[selected_user] = user_data
            st.write("User updated.")

    else:
        st.error("Unauthorized access.")


def user_page():
    st.subheader("User Page")
    st.write(f"Welcome, {users[st.session_state['user_email']]['name']}!")
    st.write("This is the regular user page.")


def employee_page():
    st.subheader("Employee Welcome Page")
    st.write(f"Welcome, {users[st.session_state['user_email']]['name']}!")
    st.write("This is the employee welcome page.")


st.set_page_config(page_title="Secure App", page_icon=":lock:", layout="wide")
st.markdown(
    """
    <style>
    .stApp {
        background-color: #222;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.empty() #Hide sidebar

# Placeholder for company logo
st.image(".\images\logo_propor.jpg", width=200) #Replace with your logo


if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
    signup()
    forgot_password()
else:
    if st.session_state["user_email"] == "admin@example.com" and hash_password(st.text_input("Admin Password", type="password")) == admin_password:
        admin_panel()
    elif users[st.session_state["user_email"]]["group"] == "employees":
        employee_page()
    else:
        user_page()
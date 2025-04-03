import streamlit as st
import pandas as pd
import datetime
import os
from typing import Optional

# File paths
APPLICANTS_FILE = "onms_applicants.xlsx"
USERS_FILE = "onms_users.xlsx"

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.username = None
if 'add_form_submitted' not in st.session_state:
    st.session_state.add_form_submitted = False  # For Add Applicant
if 'update_form_submitted' not in st.session_state:
    st.session_state.update_form_submitted = False  # For Update Applicant
if 'delete_form_submitted' not in st.session_state:
    st.session_state.delete_form_submitted = False  # For Delete Applicant
if 'user_form_submitted' not in st.session_state:
    st.session_state.user_form_submitted = False  # For User Management

# Load and save functions
def load_applicants() -> pd.DataFrame:
    if os.path.exists(APPLICANTS_FILE):
        df = pd.read_excel(APPLICANTS_FILE)
        required_cols = ['Name', 'Contact_Number', 'Address', 'ID_Number', 'Email_Address', 
                         'Country_of_Interest', 'Type_of_Visa', 'Education_Level', 'Diploma', 
                         'Work_Experience', 'Current_Job', 'Travel_History', 'Any_Refusal', 
                         'Signature', 'Date', 'BDM_Name', 'Entered_By']
        for col in required_cols:
            if col not in df.columns:
                df[col] = ''
        df = df.fillna('')  # Fill NaN with empty strings
        df['ID_Number'] = df['ID_Number'].astype(str)  # Ensure ID_Number is string
        return df
    return pd.DataFrame(columns=['Name', 'Contact_Number', 'Address', 'ID_Number', 'Email_Address', 
                                 'Country_of_Interest', 'Type_of_Visa', 'Education_Level', 'Diploma', 
                                 'Work_Experience', 'Current_Job', 'Travel_History', 'Any_Refusal', 
                                 'Signature', 'Date', 'BDM_Name', 'Entered_By'])

def load_users() -> pd.DataFrame:
    if os.path.exists(USERS_FILE):
        return pd.read_excel(USERS_FILE)
    return pd.DataFrame(columns=['Username', 'Password', 'Role'])

def save_data(df: pd.DataFrame, filepath: str) -> bool:
    try:
        df.to_excel(filepath, index=False)
        return True
    except Exception as e:
        st.error(f"Failed to save data: {str(e)}")
        return False

# Function to generate a unique ID_Number
def generate_unique_id(applicants_df: pd.DataFrame) -> str:
    prefix = "ONMS"
    if applicants_df.empty or 'ID_Number' not in applicants_df.columns or applicants_df['ID_Number'].str.strip().eq('').all():
        return f"{prefix}0001"
    else:
        valid_ids = applicants_df['ID_Number'].dropna().astype(str)
        valid_ids = valid_ids[valid_ids.str.startswith(prefix)]
        if valid_ids.empty:
            return f"{prefix}0001"
        numeric_parts = valid_ids.str.replace(prefix, '', regex=False).astype(int)
        next_id = numeric_parts.max() + 1
        return f"{prefix}{next_id:04d}"  # Ensures 4-digit padding

# Authentication
def authenticate(username: str, password: str) -> Optional[str]:
    users_df = load_users()
    user = users_df[(users_df['Username'] == username) & (users_df['Password'] == password)]
    if not user.empty:
        return user.iloc[0]['Role']
    return None

# CRUD Operations
def create_applicant(applicants_df: pd.DataFrame, new_data: dict) -> pd.DataFrame:
    new_applicant = pd.DataFrame([new_data])
    return pd.concat([applicants_df, new_applicant], ignore_index=True)

def read_applicants(applicants_df: pd.DataFrame, bdm_name: str = None) -> pd.DataFrame:
    if bdm_name:
        return applicants_df[applicants_df['BDM_Name'] == bdm_name]
    return applicants_df

def update_applicant(applicants_df: pd.DataFrame, index: int, updated_data: dict) -> pd.DataFrame:
    for key, value in updated_data.items():
        applicants_df.at[index, key] = value
    return applicants_df

def delete_applicant(applicants_df: pd.DataFrame, name: str) -> pd.DataFrame:
    return applicants_df[applicants_df['Name'] != name]

# Main app
def main():
    if not st.session_state.authenticated:
        st.title("ONMS Immigration - Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            role = authenticate(username, password)
            if role:
                st.session_state.authenticated = True
                st.session_state.user_role = role
                st.session_state.username = username
                st.success(f"Logged in successfully as {username}!")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")
        return

    st.title("ONMS Immigration CRM")
    applicants_df = load_applicants()
    users_df = load_users()

    if applicants_df.empty:
        st.warning("No applicants found. Please add an applicant to get started.")
    if users_df.empty:
        st.error("No users found. Please ensure users are added.")

    menu_options = ["Dashboard", "Manage Applicants"]
    if st.session_state.user_role == "Master":
        menu_options.append("User Management")
    choice = st.sidebar.selectbox("Menu", menu_options)

    # Dashboard (Read Operation)
    if choice == "Dashboard":
        st.subheader("Dashboard")
        if st.session_state.user_role == "Master":
            st.write("All Applicants:")
            st.dataframe(read_applicants(applicants_df))
        else:
            user_applicants = read_applicants(applicants_df, st.session_state.username)
            if user_applicants.empty:
                st.info("No applicants assigned to you.")
            else:
                st.write("Your Assigned Applicants:")
                st.dataframe(user_applicants)

    # Manage Applicants (Create, Update, Delete Operations)
    elif choice == "Manage Applicants":
        st.subheader("Manage Applicants")
        tabs = st.tabs(["Add Applicant", "Update Applicant"] + (["Delete Applicant"] if st.session_state.user_role == "Master" else []))

        # Create Operation
        with tabs[0]:
            st.write("Add New Applicant")
            with st.form("new_applicant_form"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Name")
                    contact_number = st.text_input("Contact Number")
                    address = st.text_area("Address")
                    email_address = st.text_input("Email Address")
                with col2:
                    country_of_interest = st.text_input("Country of Interest")
                    type_of_visa = st.selectbox("Type of Visa", ["Student", "Visit", "PR", "Jobseeker", "Business"])
                    education_level = st.text_input("Education Level")
                    diploma = st.selectbox("Diploma", ["Yes", "No"])
                    work_experience = st.text_input("Work Experience")
                current_job = st.text_input("Current Job")
                travel_history = st.text_area("Travel History")
                any_refusal = st.text_input("Any Refusal")
                signature = st.text_input("Signature")
                date = st.date_input("Date", value=datetime.date.today())
                bdm_name = st.selectbox("BDM Name", users_df['Username'].tolist()) if not users_df.empty else ""

                submit_button = st.form_submit_button("Add Applicant")

                if submit_button and not st.session_state.add_form_submitted:
                    if not name:
                        st.error("Name is required!")
                    elif not bdm_name:
                        st.error("Please assign a BDM.")
                    else:
                        id_number = generate_unique_id(applicants_df)
                        new_data = {
                            'Name': name, 'Contact_Number': contact_number, 'Address': address,
                            'ID_Number': id_number, 'Email_Address': email_address,
                            'Country_of_Interest': country_of_interest, 'Type_of_Visa': type_of_visa,
                            'Education_Level': education_level, 'Diploma': diploma,
                            'Work_Experience': work_experience, 'Current_Job': current_job,
                            'Travel_History': travel_history, 'Any_Refusal': any_refusal,
                            'Signature': signature, 'Date': date, 'BDM_Name': bdm_name,
                            'Entered_By': st.session_state.username
                        }
                        applicants_df = create_applicant(applicants_df, new_data)
                        if save_data(applicants_df, APPLICANTS_FILE):
                            st.success(f"Applicant added successfully with ID: {id_number} by {st.session_state.username}!")
                            st.session_state.add_form_submitted = True
                        else:
                            st.error("Failed to add applicant!")
            # Reset button outside the form
            if st.session_state.add_form_submitted and st.button("Reset Add Form"):
                st.session_state.add_form_submitted = False
                st.experimental_rerun()

        # Update Operation
        with tabs[1]:
            st.write("Update Applicant")
            if applicants_df.empty:
                st.info("No applicants available to update.")
            else:
                applicant_names = applicants_df['Name'].tolist()
                selected_applicant = st.selectbox("Select Applicant to Update", applicant_names)
                applicant_index = applicant_names.index(selected_applicant)
                current_data = applicants_df.iloc[applicant_index]

                if st.session_state.user_role != "Master" and current_data['BDM_Name'] != st.session_state.username:
                    st.error("You can only update your assigned applicants.")
                else:
                    with st.form("update_applicant_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            name = st.text_input("Name", value=current_data['Name'], disabled=(st.session_state.user_role != "Master"))
                            contact_number = st.text_input("Contact Number", value=current_data['Contact_Number'], disabled=(st.session_state.user_role != "Master"))
                            address = st.text_area("Address", value=current_data['Address'], disabled=(st.session_state.user_role != "Master"))
                            st.write(f"**ID Number:** {current_data['ID_Number']}")
                            email_address = st.text_input("Email Address", value=current_data['Email_Address'], disabled=(st.session_state.user_role != "Master"))
                        with col2:
                            country_of_interest = st.text_input("Country of Interest", value=current_data['Country_of_Interest'], disabled=(st.session_state.user_role != "Master"))
                            type_of_visa = st.selectbox("Type of Visa", ["Student", "Visit", "PR", "Jobseeker", "Business"],
                                                        index=["Student", "Visit", "PR", "Jobseeker", "Business"].index(current_data['Type_of_Visa']),
                                                        disabled=(st.session_state.user_role != "Master"))
                            education_level = st.text_input("Education Level", value=current_data['Education_Level'], disabled=(st.session_state.user_role != "Master"))
                            diploma = st.selectbox("Diploma", ["Yes", "No"],
                                                   index=["Yes", "No"].index(current_data['Diploma']),
                                                   disabled=(st.session_state.user_role != "Master"))
                            work_experience = st.text_input("Work Experience", value=current_data['Work_Experience'], disabled=(st.session_state.user_role != "Master"))

                        current_job = st.text_input("Current Job", value=current_data['Current_Job'], disabled=(st.session_state.user_role != "Master"))
                        travel_history = st.text_area("Travel History", value=current_data['Travel_History'], disabled=(st.session_state.user_role != "Master"))
                        any_refusal = st.text_input("Any Refusal", value=current_data['Any_Refusal'], disabled=(st.session_state.user_role != "Master"))
                        signature = st.text_input("Signature", value=current_data['Signature'], disabled=(st.session_state.user_role != "Master"))
                        date = st.date_input("Date", value=pd.to_datetime(current_data['Date']).date() if pd.notna(current_data['Date']) else datetime.date.today(),
                                             disabled=(st.session_state.user_role != "Master"))
                        st.write(f"**Entered By:** {current_data['Entered_By']}")
                        bdm_name = st.selectbox("BDM Name", users_df['Username'].tolist(),
                                                index=users_df['Username'].tolist().index(current_data['BDM_Name']) if current_data['BDM_Name'] in users_df['Username'].tolist() else 0,
                                                disabled=(st.session_state.user_role != "Master")) if not users_df.empty else current_data['BDM_Name']

                        submit_button = st.form_submit_button("Update Applicant")

                        if submit_button and not st.session_state.update_form_submitted:
                            if not name:
                                st.error("Name is required!")
                            else:
                                updated_data = {
                                    'Name': name, 'Contact_Number': contact_number, 'Address': address,
                                    'ID_Number': current_data['ID_Number'],
                                    'Email_Address': email_address,
                                    'Country_of_Interest': country_of_interest, 'Type_of_Visa': type_of_visa,
                                    'Education_Level': education_level, 'Diploma': diploma,
                                    'Work_Experience': work_experience, 'Current_Job': current_job,
                                    'Travel_History': travel_history, 'Any_Refusal': any_refusal,
                                    'Signature': signature, 'Date': date, 'BDM_Name': bdm_name,
                                    'Entered_By': st.session_state.username
                                }
                                applicants_df = update_applicant(applicants_df, applicant_index, updated_data)
                                if save_data(applicants_df, APPLICANTS_FILE):
                                    st.success(f"Applicant updated successfully by {st.session_state.username}!")
                                    st.session_state.update_form_submitted = True
                                else:
                                    st.error("Failed to update applicant!")
                    # Reset button outside the form
                    if st.session_state.update_form_submitted and st.button("Reset Update Form"):
                        st.session_state.update_form_submitted = False
                        st.experimental_rerun()

        # Delete Operation (Only for Master)
        if st.session_state.user_role == "Master" and len(tabs) > 2:
            with tabs[2]:
                st.write("Delete Applicant")
                if applicants_df.empty:
                    st.info("No applicants available to delete.")
                else:
                    selected_applicant = st.selectbox("Select Applicant to Delete", applicants_df['Name'].tolist())
                    with st.form("delete_applicant_form"):
                        submit_button = st.form_submit_button("Delete Applicant")
                        if submit_button and not st.session_state.delete_form_submitted:
                            applicants_df = delete_applicant(applicants_df, selected_applicant)
                            if save_data(applicants_df, APPLICANTS_FILE):
                                st.success(f"Applicant {selected_applicant} deleted successfully!")
                                st.session_state.delete_form_submitted = True
                            else:
                                st.error("Failed to delete applicant!")
                    # Reset button outside the form
                    if st.session_state.delete_form_submitted and st.button("Reset Delete Form"):
                        st.session_state.delete_form_submitted = False
                        st.experimental_rerun()

    # User Management (for Master users)
    elif choice == "User Management" and st.session_state.user_role == "Master":
        st.subheader("User Management")
        with st.form("user_form"):
            new_username = st.text_input("New Username")
            new_password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["Master", "Normal"])
            if st.form_submit_button("Add User") and not st.session_state.user_form_submitted:
                if new_username in users_df['Username'].values:
                    st.error("Username already exists!")
                elif not new_username or not new_password:
                    st.error("Username and password cannot be empty!")
                else:
                    new_user = pd.DataFrame({'Username': [new_username], 'Password': [new_password], 'Role': [role]})
                    if save_data(pd.concat([users_df, new_user], ignore_index=True), USERS_FILE):
                        st.success(f"User {new_username} added successfully!")
                        st.session_state.user_form_submitted = True
                    else:
                        st.error("Failed to add user!")
        # Reset button outside the form
        if st.session_state.user_form_submitted and st.button("Reset User Add Form"):
            st.session_state.user_form_submitted = False
            st.experimental_rerun()

        st.write("Current Users:")
        if not users_df.empty:
            for i, row in users_df.iterrows():
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                col1.write(row['Username'])
                col2.write(row['Role'])
                col3.write("****")
                if row['Username'] != st.session_state.username:
                    if col4.button("Delete", key=f"del_{i}") and not st.session_state.user_form_submitted:
                        applicants_df.loc[applicants_df['BDM_Name'] == row['Username'], 'BDM_Name'] = ''
                        save_data(applicants_df, APPLICANTS_FILE)
                        users_df = users_df[users_df['Username'] != row['Username']]
                        if save_data(users_df, USERS_FILE):
                            st.success(f"User {row['Username']} deleted!")
                            st.session_state.user_form_submitted = True
                        else:
                            st.error("Failed to delete user!")
            # Reset button outside the loop for user deletion
            if st.session_state.user_form_submitted and st.button("Reset User Delete Form"):
                st.session_state.user_form_submitted = False
                st.experimental_rerun()
        else:
            st.write("No users found.")
            
if __name__ == "__main__":
    if not os.path.exists(APPLICANTS_FILE):
        initial_applicants = pd.DataFrame([
            ['John Doe', '+1234567890', '123 Main St', 'ONMS0001', 'john.doe@example.com', 
             'Canada', 'Student', 'Bachelor', 'Yes', '2 years', 'Software Engineer', 
             'USA, UK', 'No', 'John Doe', datetime.date.today(), 'admin', 'admin']
        ], columns=['Name', 'Contact_Number', 'Address', 'ID_Number', 'Email_Address', 
                    'Country_of_Interest', 'Type_of_Visa', 'Education_Level', 'Diploma', 
                    'Work_Experience', 'Current_Job', 'Travel_History', 'Any_Refusal', 
                    'Signature', 'Date', 'BDM_Name', 'Entered_By'])
        save_data(initial_applicants, APPLICANTS_FILE)

    if not os.path.exists(USERS_FILE):
        initial_users = pd.DataFrame([
            {'Username': 'admin', 'Password': 'admin123', 'Role': 'Master'},
            {'Username': 'john', 'Password': 'pass123', 'Role': 'Normal'}
        ])
        save_data(initial_users, USERS_FILE)

    main()

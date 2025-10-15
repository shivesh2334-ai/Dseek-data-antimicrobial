import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Clinical Data Collection",
    page_icon="🏥",
    layout="wide"
)

# Google Sheets setup
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

def connect_to_gsheet():
    """Connect to Google Sheets using service account credentials"""
    try:
        # Create credentials from secrets
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(st.secrets["spreadsheet_id"])
        return spreadsheet.sheet1
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

def append_to_sheet(sheet, data):
    """Append new data to Google Sheet"""
    try:
        # Get current data to find next row
        existing_data = sheet.get_all_values()
        next_row = len(existing_data) + 1 if existing_data else 1
        
        # Append new row
        sheet.append_row(data)
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False

# Main application
def main():
    st.title("🏥 Clinical Data Collection for ML Training")
    st.markdown("Enter patient data for antimicrobial resistance research")
    
    # Initialize session state
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False
    
    # Connect to Google Sheets
    sheet = connect_to_gsheet()
    if not sheet:
        st.error("Cannot connect to Google Sheets. Please check configuration.")
        return
    
    with st.form("clinical_data_form"):
        st.header("Patient Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            age = st.number_input("Age", min_value=0, max_value=120, value=30)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            species = st.selectbox(
                "Species", 
                ["Escherichia coli", "Klebsiella spp.", "Pseudomonas spp.", "Other"]
            )
            setting = st.selectbox(
                "Clinical Setting", 
                ["ICU", "Internal Medicine", "Surgery", "Emergency", "Other"]
            )
            acquisition = st.selectbox(
                "Acquisition", 
                ["Community", "Hospital", "Healthcare-associated"]
            )
            
        with col2:
            bsi_source = st.selectbox(
                "BSI Source", 
                ["Primary", "Lung", "Abdomen", "UTI", "Skin/Soft Tissue", "Other"]
            )
            rectal_cpe_pos = st.radio("Rectal CPE Positive", ["No", "Yes"])
            immunosuppressed = st.radio("Immunosuppressed", ["No", "Yes"])
        
        st.header("Comorbidities")
        col3, col4, col5, col6 = st.columns(4)
        
        with col3:
            chf = st.radio("CHF", ["No", "Yes"])
        with col4:
            ckd = st.radio("CKD", ["No", "Yes"])
        with col5:
            tumor = st.radio("Tumor", ["No", "Yes"])
        with col6:
            diabetes = st.radio("Diabetes", ["No", "Yes"])
        
        st.header("Resistance Patterns (Lab Results)")
        col7, col8, col9, col10 = st.columns(4)
        
        with col7:
            cr = st.radio("Carbapenem Resistant", ["No", "Yes"])
        with col8:
            blbli_r = st.radio("BLBLI Resistant", ["No", "Yes"])
        with col9:
            fqr = st.radio("Fluoroquinolone Resistant", ["No", "Yes"])
        with col10:
            three_gc_r = st.radio("3rd Gen Cephalosporin Resistant", ["No", "Yes"])
        
        # Submit button
        submitted = st.form_submit_button("Submit Patient Data")
        
        if submitted:
            # Convert responses to numeric values
            data = [
                age,
                gender,
                species,
                1 if rectal_cpe_pos == "Yes" else 0,
                setting,
                acquisition,
                bsi_source,
                1 if chf == "Yes" else 0,
                1 if ckd == "Yes" else 0,
                1 if tumor == "Yes" else 0,
                1 if diabetes == "Yes" else 0,
                1 if immunosuppressed == "Yes" else 0,
                1 if cr == "Yes" else 0,
                1 if blbli_r == "Yes" else 0,
                1 if fqr == "Yes" else 0,
                1 if three_gc_r == "Yes" else 0,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Timestamp
            ]
            
            # Save to Google Sheets
            if append_to_sheet(sheet, data):
                st.session_state.submitted = True
                st.success("✅ Patient data successfully saved!")
            else:
                st.error("❌ Failed to save data. Please try again.")
    
    # Display current data
    st.header("Current Dataset")
    try:
        existing_data = sheet.get_all_values()
        if existing_data:
            # Create headers
            headers = [
                'Age', 'Gender', 'Species', 'Rectal_CPE_Pos', 'Setting', 'Acquisition',
                'BSI_Source', 'CHF', 'CKD', 'Tumor', 'Diabetes', 'Immunosuppressed',
                'CR', 'BLBLI_R', 'FQR', '3GC_R', 'Timestamp'
            ]
            
            # Create DataFrame (skip header row if it exists)
            if len(existing_data) > 1:
                df = pd.DataFrame(existing_data[1:], columns=headers)
                
                # Convert numeric columns
                numeric_cols = ['Age', 'Rectal_CPE_Pos', 'CHF', 'CKD', 'Tumor', 'Diabetes', 
                               'Immunosuppressed', 'CR', 'BLBLI_R', 'FQR', '3GC_R']
                for col in numeric_cols:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                st.dataframe(df, use_container_width=True)
                
                # Show basic statistics
                st.subheader("Dataset Summary")
                col11, col12, col13 = st.columns(3)
                
                with col11:
                    st.metric("Total Patients", len(df))
                with col12:
                    st.metric("CPE Positive", f"{df['Rectal_CPE_Pos'].sum()} ({df['Rectal_CPE_Pos'].mean()*100:.1f}%)")
                with col13:
                    st.metric("Average Age", f"{df['Age'].mean():.1f}")
                
                # Download option
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Data as CSV",
                    data=csv,
                    file_name=f"clinical_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No patient data collected yet. Submit the first entry above.")
        else:
            st.info("No data available yet. Start by submitting patient data above.")
            
    except Exception as e:
        st.error(f"Error loading existing data: {e}")

if __name__ == "__main__":
    main()

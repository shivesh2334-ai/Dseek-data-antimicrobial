import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time
from gspread.exceptions import APIError, SpreadsheetNotFound

# Page configuration
st.set_page_config(
    page_title="Clinical Data Collection",
    page_icon="🏥",
    layout="wide"
)

# Google Sheets setup
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource(ttl=3600)  # Cache connection for 1 hour
def connect_to_gsheet():
    """Connect to Google Sheets using service account credentials with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Create credentials from secrets
            creds_dict = st.secrets["gcp_service_account"]
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
            client = gspread.authorize(creds)
            spreadsheet = client.open_by_key(st.secrets["spreadsheet_id"])
            
            # Test connection
            spreadsheet.title
            st.success("✅ Successfully connected to Google Sheets")
            return spreadsheet.sheet1
            
        except SpreadsheetNotFound:
            st.error(f"❌ Spreadsheet not found. Please check the spreadsheet ID.")
            return None
        except APIError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                st.warning(f"⚠️ API error, retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                st.error(f"❌ Failed to connect after {max_retries} attempts: {e}")
                return None
        except Exception as e:
            st.error(f"❌ Unexpected error connecting to Google Sheets: {e}")
            return None

def append_to_sheet(sheet, data):
    """Append new data to Google Sheet with error handling"""
    try:
        # Append new row
        sheet.append_row(data, value_input_option='USER_ENTERED')
        
        # Verify the data was added by checking the last row
        all_data = sheet.get_all_values()
        if all_data and len(all_data) > 1:
            last_row = all_data[-1]
            if str(data[0]) == last_row[0]:  # Check if age matches
                return True
        return False
        
    except APIError as e:
        st.error(f"❌ Google Sheets API error: {e}")
        return False
    except Exception as e:
        st.error(f"❌ Error saving data: {e}")
        return False

@st.cache_data(ttl=300)  # Cache data for 5 minutes
def get_sheet_data(sheet):
    """Get all data from Google Sheet with caching"""
    try:
        records = sheet.get_all_records()
        return records
    except Exception as e:
        st.error(f"❌ Error loading data from sheet: {e}")
        return []

def validate_form_data(age, gender, species, setting, acquisition, bsi_source):
    """Validate form data before submission"""
    errors = []
    
    if age < 0 or age > 120:
        errors.append("Age must be between 0 and 120")
    
    if not gender:
        errors.append("Gender is required")
    
    if not species:
        errors.append("Species is required")
    
    if not setting:
        errors.append("Clinical setting is required")
    
    if not acquisition:
        errors.append("Acquisition type is required")
    
    if not bsi_source:
        errors.append("BSI source is required")
    
    return errors

def clear_form():
    """Clear form inputs by resetting session state"""
    st.session_state.submitted = True
    # Note: For actual form clearing, we'd need to use form key reset
    # This is a limitation of Streamlit forms

# Main application
def main():
    st.title("🏥 Clinical Data Collection for ML Training")
    st.markdown("Enter patient data for antimicrobial resistance research")
    
    # Initialize session state
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False
    if 'last_submission_time' not in st.session_state:
        st.session_state.last_submission_time = None
    
    # Connect to Google Sheets
    with st.spinner("Connecting to Google Sheets..."):
        sheet = connect_to_gsheet()
    
    if not sheet:
        st.error("""
        Cannot connect to Google Sheets. Please check:
        1. Google Sheets API is enabled
        2. Service account has editor access to the sheet
        3. Spreadsheet ID is correct
        4. Internet connection is available
        """)
        return
    
    # Data entry form
    with st.form("clinical_data_form", clear_on_submit=True):
        st.header("Patient Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            age = st.number_input("Age*", min_value=0, max_value=120, value=30, 
                                help="Patient age in years")
            gender = st.selectbox("Gender*", ["", "Male", "Female", "Other"], 
                                help="Patient gender")
            species = st.selectbox(
                "Species*", 
                ["", "Escherichia coli", "Klebsiella spp.", "Pseudomonas spp.", "Other"],
                help="Bacterial species"
            )
            setting = st.selectbox(
                "Clinical Setting*", 
                ["", "ICU", "Internal Medicine", "Surgery", "Emergency", "Other"],
                help="Clinical setting where infection was identified"
            )
            acquisition = st.selectbox(
                "Acquisition*", 
                ["", "Community", "Hospital", "Healthcare-associated"],
                help="How the infection was acquired"
            )
            
        with col2:
            bsi_source = st.selectbox(
                "BSI Source*", 
                ["", "Primary", "Lung", "Abdomen", "UTI", "Skin/Soft Tissue", "Other"],
                help="Source of bloodstream infection"
            )
            rectal_cpe_pos = st.radio("Rectal CPE Positive*", ["No", "Yes"],
                                    help="Rectal screening for carbapenemase-producing Enterobacteriaceae")
            immunosuppressed = st.radio("Immunosuppressed*", ["No", "Yes"],
                                      help="Patient immunosuppression status")
        
        st.header("Comorbidities")
        col3, col4, col5, col6 = st.columns(4)
        
        with col3:
            chf = st.radio("CHF*", ["No", "Yes"], 
                         help="Congestive Heart Failure")
        with col4:
            ckd = st.radio("CKD*", ["No", "Yes"],
                         help="Chronic Kidney Disease")
        with col5:
            tumor = st.radio("Tumor*", ["No", "Yes"],
                           help="Presence of tumor")
        with col6:
            diabetes = st.radio("Diabetes*", ["No", "Yes"],
                              help="Diabetes status")
        
        st.header("Resistance Patterns (Lab Results)")
        col7, col8, col9, col10 = st.columns(4)
        
        with col7:
            cr = st.radio("Carbapenem Resistant*", ["No", "Yes"],
                        help="Carbapenem resistance")
        with col8:
            blbli_r = st.radio("BLBLI Resistant*", ["No", "Yes"],
                             help="Beta-lactam/beta-lactamase inhibitor resistance")
        with col9:
            fqr = st.radio("Fluoroquinolone Resistant*", ["No", "Yes"],
                         help="Fluoroquinolone resistance")
        with col10:
            three_gc_r = st.radio("3rd Gen Cephalosporin Resistant*", ["No", "Yes"],
                                help="3rd generation cephalosporin resistance")
        
        st.markdown("**Required fields*")
        
        # Submit button
        submitted = st.form_submit_button("📋 Submit Patient Data")
        
        if submitted:
            # Validate required fields
            validation_errors = validate_form_data(age, gender, species, setting, acquisition, bsi_source)
            
            if validation_errors:
                for error in validation_errors:
                    st.error(f"❌ {error}")
            else:
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
                
                # Show progress and save to Google Sheets
                with st.spinner("Saving patient data..."):
                    if append_to_sheet(sheet, data):
                        st.session_state.submitted = True
                        st.session_state.last_submission_time = datetime.now()
                        st.success("✅ Patient data successfully saved!")
                        
                        # Show success message for 3 seconds
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Failed to save data. Please try again.")
    
    # Display current data
    st.header("📊 Current Dataset")
    
    try:
        # Refresh data button
        col_refresh, col_stats = st.columns([1, 3])
        with col_refresh:
            if st.button("🔄 Refresh Data"):
                st.cache_data.clear()
                st.rerun()
        
        # Load data with caching
        with st.spinner("Loading data..."):
            records = get_sheet_data(sheet)
        
        if records:
            df = pd.DataFrame(records)
            
            if not df.empty:
                # Display data
                st.dataframe(df, use_container_width=True, height=400)
                
                # Show basic statistics
                st.subheader("📈 Dataset Summary")
                col11, col12, col13, col14 = st.columns(4)
                
                with col11:
                    st.metric("Total Patients", len(df))
                with col12:
                    cpe_pos_rate = df.get('Rectal_CPE_Pos', pd.Series([0])).mean() * 100
                    st.metric("CPE Positive Rate", f"{cpe_pos_rate:.1f}%")
                with col13:
                    avg_age = df.get('Age', pd.Series([0])).mean()
                    st.metric("Average Age", f"{avg_age:.1f}")
                with col14:
                    resistant_patients = df.get('CR', pd.Series([0])).sum()
                    st.metric("Carbapenem Resistant", resistant_patients)
                
                # Additional statistics
                st.subheader("📋 Data Overview")
                col21, col22 = st.columns(2)
                
                with col21:
                    st.write("**Species Distribution**")
                    species_counts = df.get('Species', pd.Series([])).value_counts()
                    st.bar_chart(species_counts)
                
                with col22:
                    st.write("**Setting Distribution**")
                    setting_counts = df.get('Setting', pd.Series([])).value_counts()
                    st.bar_chart(setting_counts)
                
                # Download option
                st.subheader("💾 Export Data")
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Data as CSV",
                    data=csv,
                    file_name=f"clinical_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    help="Download complete dataset for analysis"
                )
                
                # Data quality check
                st.subheader("🔍 Data Quality")
                missing_data = df.isnull().sum().sum()
                if missing_data > 0:
                    st.warning(f"⚠️ Dataset contains {missing_data} missing values")
                else:
                    st.success("✅ No missing values detected")
                    
            else:
                st.info("📝 No patient data collected yet. Submit the first entry above.")
        else:
            st.info("📝 No data available yet. Start by submitting patient data above.")
            
    except Exception as e:
        st.error(f"❌ Error processing data: {e}")
        st.info("💡 Try refreshing the data or check your Google Sheets connection")

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
            <p>Clinical Data Collection System | For Research Use Only</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
    

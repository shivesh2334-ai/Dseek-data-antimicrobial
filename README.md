# Clinical Data Collection for ML Training

A Streamlit web application for collecting real clinical data related to antimicrobial resistance patterns. This application mimics the structure of synthetic data used for machine learning training and stores the data in Google Sheets.

## Features

- **Patient Data Collection**: Capture comprehensive clinical information including demographics, comorbidities, and resistance patterns
- **Google Sheets Integration**: Automatically stores data in Google Sheets for persistence
- **Real-time Data Preview**: View collected data directly in the application
- **CSV Export**: Download collected data for analysis and ML training
- **Responsive Design**: User-friendly interface optimized for clinical data entry

## Data Structure

The application collects the following fields:

### Patient Information
- Age
- Gender
- Species (Escherichia coli, Klebsiella spp., Pseudomonas spp., Other)
- Rectal CPE Positive
- Clinical Setting (ICU, Internal Medicine, Surgery, etc.)
- Acquisition (Community, Hospital, Healthcare-associated)
- BSI Source (Primary, Lung, Abdomen, UTI, etc.)

### Comorbidities
- CHF (Congestive Heart Failure)
- CKD (Chronic Kidney Disease)
- Tumor
- Diabetes
- Immunosuppressed status

### Resistance Patterns
- Carbapenem Resistant (CR)
- BLBLI Resistant
- Fluoroquinolone Resistant (FQR)
- 3rd Gen Cephalosporin Resistant (3GC_R)

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- Google Cloud Platform account
- Google Sheets API enabled

### 2. Installation

1. Clone or download this repository
2. Install required packages:
   ```bash
   pip install -r requirements.txt

# BUSINESS TRANSACTION PATTERN ANALYSIS APP

User Goals: To identify and analyze transaction patterns that may indicate business-related activities rather than personal consumption. The web application provides comprehensive data analysis, visualizations, and insights to help financial institutions better serve business customers.

## 1.

## 1.1 Key Features

- Interactive data transformation and visualization of transaction patterns
- Analysis of transaction frequency, amounts, and category distributions
- Time-series analysis with daily, weekly, monthly, seasonal, and hourly patterns
- Counterpart and MCC (Merchant Category Code) analysis for business activity detection
- Customer clustering to identify distinct business customer segments
- Detailed findings and recommendations for product development and marketing strategies

## 1.2 Additional Features
- Statistical validation of clustering results
- ROI analysis for implementing business-focused initiatives
- Customizable visualizations with multiple filtering options
- Interactive dashboards for exploring customer segments

## 2.

## 2.1 Technical Requirements
- The APP is a Streamlit application
- The APP has a requirements.txt file
- The APP uses Plotly for its interactive visualizations
- The APP uses Python 3.9+ for its coding
- The dataframes are in CSV format and manipulated using Pandas
- The APP source code is available in the project repository
- The APP can be deployed on any cloud platform supporting Streamlit

## 2.2 Data Requirements
1. The APP requires preprocessed transaction data files:
   - `preprocessed_transactions_with_mcc_desc.csv` (primary transaction data)
   - `preprocessed_share_of_wallet_per_user.csv` (customer wallet share data)
   - `preprocessed_share_of_wallet_per_user_date.csv` (time-series wallet share data)
   - `dict_mcc.json` (MCC code dictionary)

2. You must update the file paths in the yapeal_app.py file:
   - Locate lines 84, 85, and 86 in the yapeal_app.py file
   - Change the file paths from the current values to the location where you have saved your CSV files
   - Example: Change `/Users/daniellelott/Documents/Masters/Customer_Analytics/Data/preprocessed_transactions_with_mcc_desc.csv` to your local path

## 3. Technologies
- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Plotly
- Scikit-learn
- SciPy
- Streamlit

## 4.

## 4.1 Run Locally (Mac)

### 1st Step
Go to the root folder of the Project. `(Ex: cd Documents/.../Business_Transaction_Analysis)`

### 2nd Step 
Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate
```

### 3rd Step
Install the requirements from the requirements.txt file with the command: `pip install -r requirements.txt`

### 4th Step
After the requirements are installed, run the Streamlit app with the following command: `streamlit run yapeal_app.py`

## 4.2 Run Locally (Windows)

### 1st Step
Go to the root folder of the Project. `(Ex: cd Documents/.../Business_Transaction_Analysis)`

### 2nd Step 
Create and activate a virtual environment:
```
python -m venv venv
venv\Scripts\activate
```

### 3rd Step
Install the requirements from the requirements.txt file with the command: `python -m pip install -r requirements.txt`

### 4th Step
After the requirements are installed, run the Streamlit app with the following command: `python -m streamlit run yapeal_app.py`

## 5. Important Links: 
- [Main App](yapeal_app.py)
- [Requirements](requirements.txt)
- [Sample Data](data/)
- [Documentation](docs/)

## 6. Further help
You can contact the development team for further assistance through our emails and we will get back to you as soon as possible. For efficient troubleshooting, a screenshot of the error would be highly appreciated.

joel.sturzenegger@stud.hslu.ch  
daniellemaria.perezlott@stud.hslu.ch  
valeska.blank@stud.hslu.ch  
simon.welti@stud.hslu.ch  
marta.marinozzi@stud.hslu.ch
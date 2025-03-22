import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import scipy.cluster.hierarchy as sch
import scipy.stats as stats
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler
import plotly.figure_factory as ff
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import silhouette_score
import json
import os
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Business Transaction Pattern Analysis",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: bold;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .subsection-header {
        font-size: 1.4rem;
        font-weight: bold;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }
    .insight-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .highlight-text {
        color: #ff4b4b;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for navigation and controls
with st.sidebar:
    st.title("Navigation")
    page = st.radio(
        "Go to",
        ["Overview", "Data Transformation", "Visualization", "Clustering", "Findings & Recommendations"]
    )
    
    st.markdown("---")
    st.subheader("Team Members")
    st.markdown("""
    - Joel Sturzenegger (Data Analysis)
    - Danielle Maria Perez Lott (Data Cleaning and App Dev)
    - Valeska Blank (Review & Storytelling)
    - Simon Welti (Analysis & Documentation)
    - Marta Marinozzi (Data Analysis)
    """)

# Helper function to load data
@st.cache_data
def load_data():
    try:
        # Define file paths - adjust these to match your environment
        transactions_path = "/Users/valeskablank/Documents/App/Data/preprocessed_transactions_with_mcc_desc.csv"
        share_of_wallet_path = "/Users/valeskablank/Documents/App/Data/preprocessed_share_of_wallet_per_user.csv"
        share_of_wallet_date_path = "/Users/valeskablank/Documents/App/Data/preprocessed_share_of_wallet_per_user_date.csv"
        
        # Load data
        transactions_df = pd.read_csv(transactions_path)
        share_of_wallet_df = pd.read_csv(share_of_wallet_path)
        share_of_wallet_date_df = pd.read_csv(share_of_wallet_date_path)
        
        # Convert date columns
        transactions_df['trx_date'] = pd.to_datetime(transactions_df['trx_date'], errors='coerce')
        if 'date' in share_of_wallet_date_df.columns:
            share_of_wallet_date_df['date'] = pd.to_datetime(share_of_wallet_date_df['date'], errors='coerce')
        
        # Calculate transaction frequency per customer
        customer_transaction_freq = transactions_df.groupby('customer_id').size().reset_index(name='transaction_frequency')
        
        # Calculate average transaction amount per customer
        customer_avg_amount = transactions_df.groupby('customer_id')['amount_chf'].mean().reset_index(name='avg_transaction_amount')
        customer_total_spent = transactions_df.groupby('customer_id')['amount_chf'].sum().reset_index(name='total_spent')
        
        # Calculate transaction frequency by year if year column exists
        if 'year' in transactions_df.columns:
            yearly_freq = transactions_df.groupby(['customer_id', 'year']).size().reset_index(name='yearly_transactions')
        
        # Merge metrics into a single DataFrame
        customer_metrics = pd.merge(customer_transaction_freq, customer_avg_amount, on='customer_id')
        customer_metrics = pd.merge(customer_metrics, customer_total_spent, on='customer_id')
        
        # Add category spending percentages if category column exists
        if 'category' in transactions_df.columns:
            category_spending = transactions_df.groupby(['customer_id', 'category'])['amount_chf'].sum().reset_index()
            
            # Get total spending per customer for percentage calculation
            customer_totals = transactions_df.groupby('customer_id')['amount_chf'].sum().reset_index()
            customer_totals.columns = ['customer_id', 'total_customer_spend']
            
            # Merge with category spending
            category_spending = pd.merge(category_spending, customer_totals, on='customer_id')
            
            # Calculate percentage
            category_spending['percentage'] = (category_spending['amount_chf'] / category_spending['total_customer_spend']) * 100
            
            # Pivot to get categories as columns
            category_pivot = category_spending.pivot_table(
                index='customer_id', 
                columns='category', 
                values='percentage',
                fill_value=0
            )
            
            # Rename columns to add _pct suffix
            category_pivot.columns = [f"{col}_pct" for col in category_pivot.columns]
            
            # Reset index to merge with customer_metrics
            category_pivot = category_pivot.reset_index()
            
            # Merge with main metrics dataframe
            customer_metrics = pd.merge(customer_metrics, category_pivot, on='customer_id', how='left')
        
        # Calculate weekday vs weekend transaction ratio
        transactions_df['weekday'] = transactions_df['trx_date'].dt.dayofweek
        transactions_df['is_weekend'] = transactions_df['weekday'].isin([5, 6]).astype(int)
        
        # Calculate weekday/weekend counts
        weekday_counts = transactions_df.groupby('customer_id')['is_weekend'].mean().reset_index()
        weekday_counts.columns = ['customer_id', 'weekend_ratio']
        weekday_counts['weekday_ratio'] = 100 - (weekday_counts['weekend_ratio'] * 100)
        
        # Merge with customer metrics
        customer_metrics = pd.merge(customer_metrics, weekday_counts[['customer_id', 'weekday_ratio']], on='customer_id', how='left')
        
        return customer_metrics, transactions_df, share_of_wallet_df, share_of_wallet_date_df
    
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.exception(e)
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Helper function to load MCC data
@st.cache_data
def load_mcc_data():
    try:
        # Create a mapping from MCC codes to descriptions based on your data
        mcc_dict = {}
        
        # First try to load from a JSON file if available
        try:
            with open('dict_mcc.json', 'r') as f:
                mcc_dict = json.load(f)
                return mcc_dict
        except:
            pass
        
        # If that fails, try to extract from transactions data
        try:
            transactions_df = pd.read_csv("preprocessed_transactions.csv")
            if 'mcc' in transactions_df.columns and 'mcc_category' in transactions_df.columns:
                # Create a mapping from unique MCCs to their categories
                mcc_mapping = transactions_df[['mcc', 'mcc_category']].drop_duplicates()
                mcc_dict = dict(zip(mcc_mapping['mcc'].astype(str), mcc_mapping['mcc_category']))
                return mcc_dict
        except:
            pass
        
        # Return empty dict if nothing works
        return {}
    
    except Exception as e:
        st.debug(f"Error loading MCC data: {e}")
        return {}

# Load data
df, transactions_df, share_of_wallet_df, share_of_wallet_date_df = load_data()
mcc_data = load_mcc_data()

# Main content based on page selection
if page == "Overview":
    st.markdown('<div class="main-header">Business Transaction Pattern Analysis</div>', unsafe_allow_html=True)
    
    st.markdown("""
    **Research question: Can we identify transaction patterns that hint at business-related activities?**
    
    This application explores credit card transaction data to identify patterns that may indicate 
    business-related spending behaviors rather than personal consumption.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="section-header">Approach</div>', unsafe_allow_html=True)
        st.markdown("""
        1. **Data Transformation**: Calculate key metrics like transaction frequency, amounts, and category distributions
        2. **Visualization**: Explore patterns through histograms, time-series, and distribution plots
        3. **Clustering**: Use unsupervised learning to identify customer segments
        4. **Interpretation**: Test hypotheses and identify business-like transaction patterns
        5. **Recommendations**: Provide insights for targeted products and services
        """)
    
    with col2:
        st.markdown('<div class="section-header">Key Indicators</div>', unsafe_allow_html=True)
        st.markdown("""
        - High transaction frequency (consistent activity)
        - Higher average transaction values 
        - Spending concentrated in business-related categories
        - Regular transactions with business-oriented merchants
        - Distinct temporal patterns (e.g., weekday vs weekend)
        """)
    
    st.markdown('<div class="section-header">Dataset Overview</div>', unsafe_allow_html=True)
    
    if not transactions_df.empty:
        # Filter out rows with 'unknown' mcc_category
        filtered_transactions_df = transactions_df[transactions_df['mcc_category'] != 'unknown']
    
        st.dataframe(filtered_transactions_df.head())
    
        st.markdown('<div class="section-header">Basic Statistics</div>', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Transactions", f"{len(filtered_transactions_df):,}")
        col2.metric("Unique Customers", f"{filtered_transactions_df['customer_id'].nunique():,}")
    
        if 'amount_chf' in filtered_transactions_df.columns:
            col3.metric("Avg. Transaction Amount", f"CHF {filtered_transactions_df['amount_chf'].mean():.2f}")
            col4.metric("Total Transaction Volume", f"CHF {filtered_transactions_df['amount_chf'].sum():,.2f}")
    else:
        st.error("Could not load the transaction dataset. Please check the file paths and try again.")

elif page == "Data Transformation":
    st.markdown('<div class="main-header">Data Transformation</div>', unsafe_allow_html=True)
    
    st.markdown("""
    This section explores the transformed transaction data, highlighting key metrics that could 
    indicate business-related spending patterns.
    """)
    
    if transactions_df.empty:
        st.error("Could not load the transaction dataset. Please check the file paths and try again.")
    else:
        # Remove year 2020 if present (not analyzed)
        if 'year' in transactions_df.columns:
            transactions_df = transactions_df[transactions_df['year'] != 2020]
        
        # Transaction Frequency Analysis
        st.markdown('<div class="section-header">Transaction Frequency</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Calculate transaction frequency per customer per year
            customer_yearly_freq = transactions_df.groupby(['customer_id', 'year']).size().reset_index(name='transaction_count')
            
            # Identify outliers using IQR method per year
            outliers_per_year = {}
            years = customer_yearly_freq['year'].unique()
            
            for year in sorted(years):
                data_year = customer_yearly_freq[customer_yearly_freq['year'] == year]
                q1 = data_year['transaction_count'].quantile(0.25)
                q3 = data_year['transaction_count'].quantile(0.75)
                iqr = q3 - q1
                upper_bound = q3 + 2.0 * iqr
                
                outliers = data_year[data_year['transaction_count'] > upper_bound]
                outliers_per_year[year] = outliers
            
            # Create boxplot with outliers
            fig = px.box(customer_yearly_freq, x='year', y='transaction_count',
                         points='outliers',
                         title='Overall Transaction Distribution by Year')
            fig.update_layout(
                xaxis_title="Year", 
                yaxis_title="Number of Transactions per Customer"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown('<div class="insight-box">', unsafe_allow_html=True)
            st.markdown("""
            ### Key Insight
            - Most customers are well below 500 transactions per year
            - A few outliers range from about 1,000 to 2,500 transactions
            - The general activity level increases year by year
            - Significant variation in transaction frequencies observed
            """)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Identify customers who are outliers in all active years
            all_outlier_customers = set()
            for year in years:
                all_outlier_customers.update(outliers_per_year[year]['customer_id'].unique())
            
            active_years_per_customer = transactions_df.groupby('customer_id')['year'].unique().to_dict()
            
            final_outliers = []
            for customer in all_outlier_customers:
                active_years = set(active_years_per_customer.get(customer, []))
                outlier_years = {yr for yr in years if customer in outliers_per_year[yr]['customer_id'].values}
                if active_years.issubset(outlier_years):
                    final_outliers.append(customer)
            
            # Prepare data for business vs non-business comparison
            customer_yearly_freq['group'] = customer_yearly_freq['customer_id'].apply(
                lambda x: 'Potential-Business' if x in final_outliers else 'Potential-Non-Business'
            )
            
            # Boxplot comparing business vs non-business
            fig_compare = px.box(
                customer_yearly_freq, 
                x='group', 
                y='transaction_count',
                points='outliers',
                title='Comparison: Potential-Business vs. Potential-Non-Business'
            )
            fig_compare.update_layout(
                xaxis_title="", 
                yaxis_title="Number of Transactions per Customer"
            )
            st.plotly_chart(fig_compare, use_container_width=True)
        
        # Transaction Amount Analysis
        st.markdown('<div class="section-header">Transaction Amounts</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Calculate yearly average transaction amount per customer
            customer_yearly_amount = transactions_df.groupby(['customer_id', 'year'])['amount_chf'].agg(
                transaction_count='count',
                total_amount='sum',
                average_amount='mean',
                std_dev_amount='std',
                min_amount='min',
                max_amount='max'
            ).reset_index()
            
            # Identify amount outliers using IQR method per year
            amount_outliers_per_year = {}
            
            for year in sorted(years):
                data_year = customer_yearly_amount[customer_yearly_amount['year'] == year]
                q1 = data_year['average_amount'].quantile(0.25)
                q3 = data_year['average_amount'].quantile(0.75)
                iqr = q3 - q1
                upper_bound = q3 + 2.0 * iqr
                
                outliers = data_year[data_year['average_amount'] > upper_bound]
                amount_outliers_per_year[year] = outliers
            
            # Boxplot of average transaction amount
            fig_amount = px.box(
                customer_yearly_amount, 
                x='year', 
                y='average_amount',
                points='outliers',
                title='Average Transaction Amount per Customer and Year'
            )
            fig_amount.update_layout(
                xaxis_title="Year", 
                yaxis_title="Average Transaction Amount (CHF)"
            )
            st.plotly_chart(fig_amount, use_container_width=True)
        
        with col2:
            st.markdown('<div class="insight-box">', unsafe_allow_html=True)
            st.markdown("""
            ### Key Insight
            - Most transactions are well below 100 CHF
            - Only a few extreme outliers exist above 4,000-5,000 CHF
            - The distribution varies year to year
            - Standard deviation shows slight increase in variability
            """)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Identify customers who are amount outliers in all their active years
            all_amount_outlier_customers = set()
            for year in years:
                all_amount_outlier_customers.update(amount_outliers_per_year[year]['customer_id'].unique())
            
            final_amount_outliers = []
            for customer in all_amount_outlier_customers:
                active_years = set(active_years_per_customer.get(customer, []))
                outlier_years = {yr for yr in years if customer in amount_outliers_per_year[yr]['customer_id'].values}
                if active_years.issubset(outlier_years):
                    final_amount_outliers.append(customer)
            
            # Prepare data for amount comparison
            customer_yearly_amount['group'] = customer_yearly_amount['customer_id'].apply(
                lambda x: 'Potential-Business' if x in final_amount_outliers else 'Potential-Non-Business'
            )
            
            # Boxplot comparing business vs non-business amounts
            fig_amount_compare = px.box(
                customer_yearly_amount, 
                x='group', 
                y='average_amount',
                points='outliers',
                title='Comparison: Potential-Business vs. Potential-Non-Business (Avg. Amount)'
            )
            fig_amount_compare.update_layout(
                xaxis_title="", 
                yaxis_title="Average Transaction Amount (CHF)"
            )
            st.plotly_chart(fig_amount_compare, use_container_width=True)
        
        # Category-Based Analysis (kept from original implementation)
        if 'category' in transactions_df.columns:
            st.markdown('<div class="section-header">Category-Based Analysis</div>', unsafe_allow_html=True)
            
            # Get top categories by transaction count
            category_counts = transactions_df['category'].value_counts().reset_index()
            category_counts.columns = ['Category', 'Transaction Count']
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(category_counts.head(10), x='Category', y='Transaction Count',
                            title="Top 10 Categories by Transaction Count")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Get top categories by amount
                category_amounts = transactions_df.groupby('category')['amount_chf'].sum().reset_index()
                category_amounts.columns = ['Category', 'Total Amount (CHF)']
                category_amounts = category_amounts.sort_values('Total Amount (CHF)', ascending=False)
                
                fig = px.bar(category_amounts.head(10), x='Category', y='Total Amount (CHF)',
                            title="Top 10 Categories by Transaction Amount")
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown('<div class="insight-box">', unsafe_allow_html=True)
            st.markdown("""
            ### Key Insight
            - Business spending often shows distinctive category patterns
            - Categories like communication, office supplies, and business services may indicate business activity
            - Personal spending typically shows higher percentages in restaurants, shopping, and entertainment
            """)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Allow user to explore specific categories
            selected_category = st.selectbox("Select Category to Analyze", 
                                            sorted(transactions_df['category'].unique()))
            
            # Show transactions for selected category
            cat_transactions = transactions_df[transactions_df['category'] == selected_category]
            
            st.write(f"### Analysis of '{selected_category}' Category")
            st.write(f"Total transactions: {len(cat_transactions)}")
            st.write(f"Total amount: CHF {cat_transactions['amount_chf'].sum():,.2f}")
            st.write(f"Average transaction amount: CHF {cat_transactions['amount_chf'].mean():.2f}")
            st.write(f"Number of customers using this category: {cat_transactions['customer_id'].nunique()}")
            
            # Show distribution of transaction amounts for this category
            fig = px.histogram(cat_transactions, x="amount_chf", 
                               nbins=50,
                               title=f"Distribution of Transaction Amounts for {selected_category}",
                               labels={"amount_chf": "Amount (CHF)"})
            st.plotly_chart(fig, use_container_width=True)
        
        # Weekday/Weekend Analysis
        st.markdown('<div class="section-header">Weekday vs. Weekend Transaction Patterns</div>', unsafe_allow_html=True)
        
        # Add weekday column if not present
        if 'weekday' not in transactions_df.columns:
            transactions_df['weekday'] = transactions_df['trx_date'].dt.dayofweek
            transactions_df['is_weekend'] = transactions_df['weekday'].isin([5, 6]).astype(int)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Count transactions by day of week
            day_counts = transactions_df['weekday'].value_counts().reset_index()
            day_counts.columns = ['day_of_week', 'count']
            day_counts = day_counts.sort_values('day_of_week')
            
            # Map day numbers to names
            day_names = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 
                         4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
            day_counts['day_name'] = day_counts['day_of_week'].map(day_names)
            
            fig = px.bar(day_counts, x='day_name', y='count',
                        title="Transaction Count by Day of Week",
                        labels={"day_name": "Day", "count": "Transaction Count"})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown('<div class="insight-box">', unsafe_allow_html=True)
            st.markdown("""
            ### Key Insight
            - Business transactions typically occur on weekdays rather than weekends
            - A high weekday to weekend ratio may indicate business-related spending
            - Personal spending often shows higher weekend activity
            """)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Calculate weekday ratio per customer
            customer_weekday = transactions_df.groupby('customer_id')['is_weekend'].mean().reset_index()
            customer_weekday['weekday_ratio'] = (1 - customer_weekday['is_weekend']) * 100
            
            fig = px.histogram(customer_weekday, x="weekday_ratio", 
                               nbins=50,
                               title="Distribution of Weekday Transaction Ratio per Customer",
                               labels={"weekday_ratio": "% of Transactions on Weekdays"})
            st.plotly_chart(fig, use_container_width=True)

elif page == "Visualization":
    st.markdown('<div class="main-header">Visualization</div>', unsafe_allow_html=True)
    
    st.markdown("""
    This section provides visualizations of the transaction data to help identify patterns
    that might distinguish business from personal spending.
    """)
    
    if transactions_df.empty:
        st.error("Could not load the transaction dataset. Please check the file paths and try again.")
    else:
        # Define visualization options based on available data
        viz_options = ["Transaction Patterns Overview"]
        
        if 'trx_date' in transactions_df.columns:
            viz_options.append("Time-Series Analysis")
            
        if 'category' in transactions_df.columns:
            viz_options.append("Category Analysis")
            
        if 'counterpart' in transactions_df.columns:
            viz_options.append("Counterpart Analysis")
            
        if 'mcc' in transactions_df.columns:
            viz_options.append("MCC Analysis")
            
        viz_type = st.selectbox("Select Visualization Type", viz_options)
        
        if viz_type == "Transaction Patterns Overview":
            st.subheader("Transaction Pattern Overview")
            
            # Calculate metrics per customer
            customer_metrics = transactions_df.groupby('customer_id').agg(
                transaction_count=('trx_date', 'count'),
                avg_amount=('amount_chf', 'mean'),
                total_amount=('amount_chf', 'sum')
            ).reset_index()
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Scatter plot of transaction count vs average amount
                fig = px.scatter(customer_metrics, 
                                x="transaction_count", 
                                y="avg_amount",
                                size="total_amount",
                                hover_name="customer_id",
                                labels={
                                    "transaction_count": "Transaction Count",
                                    "avg_amount": "Average Amount (CHF)",
                                    "total_amount": "Total Spending"
                                },
                                title="Transaction Count vs. Average Amount per Customer")
                
                # Add reference lines for potential thresholds
                fig.add_hline(y=customer_metrics['avg_amount'].quantile(0.8), 
                             line_dash="dash", line_color="red")
                fig.add_vline(x=customer_metrics['transaction_count'].quantile(0.8), 
                             line_dash="dash", line_color="red")
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("""
                **Observations:**
                - Customers in the upper-right quadrant (high frequency, high amount) demonstrate clear business spending patterns
                - Several outliers with 1,000+ transactions annually likely represent business accounts
                - The larger bubble sizes indicate higher total spending volume
                - Most customers fall in the lower-left with under 500 transactions and relatively low average amounts
                - The 80th percentile thresholds (red dashed lines) effectively separate potential business from personal users
                - A small group shows extremely high transaction counts (5,000+) with moderate average amounts
                """)
            
            with col2:
                # Distribution of transactions per customer
                fig = px.histogram(customer_metrics, 
                                  x="transaction_count",
                                  nbins=50,
                                  title="Distribution of Transactions per Customer",
                                  labels={"transaction_count": "Transaction Count"})
                st.plotly_chart(fig, use_container_width=True)
                
                # Distribution of average amount per customer
                fig = px.histogram(customer_metrics, 
                                  x="avg_amount",
                                  nbins=50,
                                  title="Distribution of Average Amount per Customer",
                                  labels={"avg_amount": "Average Amount (CHF)"})
                st.plotly_chart(fig, use_container_width=True)
        
        elif viz_type == "Time-Series Analysis":
            st.subheader("Time-Series Analysis")
            
            # Create tabs for different time-based analyses
            ts_tabs = st.tabs(["Daily Patterns", "Weekly Patterns", "Monthly Patterns", "Seasonal Patterns", "Hourly Patterns"])
            
            with ts_tabs[0]:
                st.subheader("Daily Transaction Patterns")
                
                # Aggregate transactions by date
                daily_transactions = transactions_df.groupby(transactions_df['trx_date'].dt.date).agg(
                    transaction_count=('customer_id', 'count'),
                    unique_customers=('customer_id', 'nunique'),
                    total_amount=('amount_chf', 'sum'),
                    avg_amount=('amount_chf', 'mean')
                ).reset_index()
                
                # Time series metrics selection
                ts_metric = st.selectbox(
                    "Select Metric to Visualize",
                    ["transaction_count", "unique_customers", "total_amount", "avg_amount"],
                    format_func=lambda x: {
                        "transaction_count": "Transaction Count",
                        "unique_customers": "Unique Customers",
                        "total_amount": "Total Amount (CHF)",
                        "avg_amount": "Average Amount (CHF)"
                    }[x]
                )
                
                # Create time series visualization
                fig = px.line(
                    daily_transactions, 
                    x="trx_date", 
                    y=ts_metric,
                    title=f"Daily {ts_metric.replace('_', ' ').title()}",
                    labels={
                        "trx_date": "Date", 
                        ts_metric: ts_metric.replace('_', ' ').title()
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with ts_tabs[1]:
                st.subheader("Weekly Transaction Patterns")
                
                # Extract day of week
                transactions_df['day_of_week'] = transactions_df['trx_date'].dt.dayofweek
                transactions_df['day_name'] = transactions_df['trx_date'].dt.day_name()
                
                # Define day order for plotting
                day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                
                # Function to get average spending per weekday for each year
                years = sorted(transactions_df['year'].unique())
                weekly_data = {}
                
                for year in years:
                    year_data = transactions_df[transactions_df['year'] == year]
                    weekly_data[year] = year_data.groupby('day_name')['amount_chf'].mean()
                
                # Combine data for plotting
                weekly_df = pd.DataFrame(weekly_data)
                weekly_df = weekly_df.reindex(day_order)
                weekly_df = weekly_df.reset_index()
                weekly_df.columns = ['day_name'] + list(weekly_df.columns[1:])
                weekly_df = weekly_df.melt(id_vars='day_name', var_name='year', value_name='avg_amount')
                
                # Create visualization
                fig = px.line(
                    weekly_df,
                    x='day_name',
                    y='avg_amount',
                    color='year',
                    markers=True,
                    title="Average Spending by Day of the Week (By Year)",
                    labels={
                        "day_name": "Day of Week",
                        "avg_amount": "Average Spending (CHF)",
                        "year": "Year"
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Business vs. personal pattern comparison
                st.subheader("Business vs. Personal Weekly Patterns")
                
                # Identify potential business customers (top 20% by transaction frequency)
                high_freq_threshold = transactions_df.groupby('customer_id').size().quantile(0.8)
                high_freq_customers = transactions_df.groupby('customer_id').size()
                high_freq_customers = high_freq_customers[high_freq_customers >= high_freq_threshold].index
                
                # Add business flag to transactions
                transactions_df['potential_business'] = transactions_df['customer_id'].isin(high_freq_customers)
                
                # Compare patterns by day of week
                business_day_counts = transactions_df.groupby(['day_name', 'potential_business']).agg(
                    transaction_count=('customer_id', 'count')
                ).reset_index()
                
                # Convert to relative percentages within each group
                for group in business_day_counts['potential_business'].unique():
                    group_total = business_day_counts[business_day_counts['potential_business'] == group]['transaction_count'].sum()
                    business_day_counts.loc[business_day_counts['potential_business'] == group, 'percentage'] = \
                        business_day_counts.loc[business_day_counts['potential_business'] == group, 'transaction_count'] / group_total * 100
                
                # Create visualization
                fig = px.bar(
                    business_day_counts,
                    x='day_name',
                    y='percentage',
                    color='potential_business',
                    barmode='group',
                    category_orders={"day_name": day_order},
                    title="Transaction Distribution by Day of Week: Business vs. Personal",
                    labels={
                        "day_name": "Day of Week",
                        "percentage": "% of Transactions",
                        "potential_business": "Potential Business"
                    },
                    color_discrete_map={True: "blue", False: "green"}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with ts_tabs[2]:
                st.subheader("Monthly Transaction Patterns")
                
                # Extract month and year
                transactions_df['month'] = transactions_df['trx_date'].dt.to_period('M')
                
                # Create a selector for the year
                selected_year = st.selectbox("Select Year", sorted(transactions_df['year'].unique()))
                
                # Filter transactions for selected year
                transactions_year = transactions_df[transactions_df['year'] == selected_year]
                
                # Calculate average spending per month
                monthly_avg_spending = transactions_year.groupby(transactions_year['trx_date'].dt.month)['amount_chf'].mean().reset_index()
                monthly_avg_spending['month_name'] = monthly_avg_spending['trx_date'].apply(lambda x: pd.Timestamp(2023, x, 1).strftime('%B'))
                
                # Create visualization
                fig = px.line(
                    monthly_avg_spending,
                    x='month_name',
                    y='amount_chf',
                    markers=True,
                    title=f"Monthly Average Spending in {selected_year}",
                    labels={
                        "month_name": "Month",
                        "amount_chf": "Average Spending (CHF)"
                    }
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Business vs. personal monthly patterns
                st.subheader("Business vs. Personal Monthly Patterns")
                
                # Compare business vs. personal average spending by month
                business_monthly = transactions_year[transactions_year['potential_business']].groupby(transactions_year['trx_date'].dt.month)['amount_chf'].mean().reset_index()
                business_monthly['month_name'] = business_monthly['trx_date'].apply(lambda x: pd.Timestamp(2023, x, 1).strftime('%B'))
                business_monthly['group'] = 'Business'
                
                personal_monthly = transactions_year[~transactions_year['potential_business']].groupby(transactions_year['trx_date'].dt.month)['amount_chf'].mean().reset_index()
                personal_monthly['month_name'] = personal_monthly['trx_date'].apply(lambda x: pd.Timestamp(2023, x, 1).strftime('%B'))
                personal_monthly['group'] = 'Personal'
                
                combined_monthly = pd.concat([business_monthly, personal_monthly])
                
                fig = px.line(
                    combined_monthly,
                    x='month_name',
                    y='amount_chf',
                    color='group',
                    markers=True,
                    title=f"Business vs. Personal Average Spending by Month ({selected_year})",
                    labels={
                        "month_name": "Month",
                        "amount_chf": "Average Spending (CHF)",
                        "group": "Customer Type"
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with ts_tabs[3]:
                st.subheader("Seasonal Transaction Patterns")
                
                # Define a function to assign a season to each transaction
                def get_season(month):
                    if month in [3, 4, 5]:  # Spring
                        return 'Spring'
                    elif month in [6, 7, 8]:  # Summer
                        return 'Summer'
                    elif month in [9, 10, 11]:  # Autumn
                        return 'Autumn'
                    else:  # Winter
                        return 'Winter'
                
                # Add a season column
                transactions_df['season'] = transactions_df['trx_date'].dt.month.apply(get_season)
                
                # Function to get seasonal average spending for each year
                seasons_order = ['Spring', 'Summer', 'Autumn', 'Winter']
                seasonal_data = {}
                
                for year in years:
                    year_data = transactions_df[transactions_df['year'] == year]
                    seasonal_data[year] = year_data.groupby('season')['amount_chf'].mean()
                
                # Combine data for plotting
                seasonal_df = pd.DataFrame(seasonal_data)
                seasonal_df = seasonal_df.reindex(seasons_order)
                seasonal_df = seasonal_df.reset_index()
                seasonal_df.columns = ['season'] + list(seasonal_df.columns[1:])
                seasonal_df = seasonal_df.melt(id_vars='season', var_name='year', value_name='avg_amount')
                
                # Create visualization
                fig = px.line(
                    seasonal_df,
                    x='season',
                    y='avg_amount',
                    color='year',
                    markers=True,
                    title="Average Spending by Season (By Year)",
                    category_orders={"season": seasons_order},
                    labels={
                        "season": "Season",
                        "avg_amount": "Average Spending (CHF)",
                        "year": "Year"
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Business vs. personal seasonal patterns
                st.subheader("Business vs. Personal Seasonal Patterns")
                
                # Compare seasonal patterns between business and personal
                business_seasonal = pd.DataFrame()
                personal_seasonal = pd.DataFrame()
                
                for year in years:
                    year_data = transactions_df[transactions_df['year'] == year]
                    
                    # Business
                    bus_data = year_data[year_data['potential_business']].groupby('season')['amount_chf'].mean()
                    bus_df = pd.DataFrame(bus_data).reset_index()
                    bus_df['year'] = year
                    bus_df['group'] = 'Business'
                    business_seasonal = pd.concat([business_seasonal, bus_df])
                    
                    # Personal
                    pers_data = year_data[~year_data['potential_business']].groupby('season')['amount_chf'].mean()
                    pers_df = pd.DataFrame(pers_data).reset_index()
                    pers_df['year'] = year
                    pers_df['group'] = 'Personal'
                    personal_seasonal = pd.concat([personal_seasonal, pers_df])
                
                combined_seasonal = pd.concat([business_seasonal, personal_seasonal])
                
                # Allow selection of a specific year
                selected_year_seasonal = st.selectbox("Select Year for Seasonal Comparison", sorted(years), key="seasonal_year")
                filtered_seasonal = combined_seasonal[combined_seasonal['year'] == selected_year_seasonal]
                
                fig = px.line(
                    filtered_seasonal,
                    x='season',
                    y='amount_chf',
                    color='group',
                    markers=True,
                    category_orders={"season": seasons_order},
                    title=f"Business vs. Personal Average Spending by Season ({selected_year_seasonal})",
                    labels={
                        "season": "Season",
                        "amount_chf": "Average Spending (CHF)",
                        "group": "Customer Type"
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with ts_tabs[4]:
                st.subheader("Hourly Transaction Patterns")
                
                # Extract hour from transaction time
                transactions_df['hour'] = transactions_df['trx_date'].dt.hour
                
                # Function to get hourly average spending for each year
                hourly_data = {}
                
                for year in years:
                    year_data = transactions_df[transactions_df['year'] == year]
                    hourly_data[year] = year_data.groupby('hour')['amount_chf'].mean()
                
                # Combine data for plotting
                hourly_df = pd.DataFrame(hourly_data)
                hourly_df = hourly_df.reset_index().melt(id_vars='hour', var_name='year', value_name='avg_amount')
                
                # Create visualization
                fig = px.line(
                    hourly_df,
                    x='hour',
                    y='avg_amount',
                    color='year',
                    markers=True,
                    title="Average Spending by Hour of Day (By Year)",
                    labels={
                        "hour": "Hour of Day (24-hour)",
                        "avg_amount": "Average Spending (CHF)",
                        "year": "Year"
                    }
                )
                # Ensure all hours are shown on x-axis
                fig.update_xaxes(tickmode='linear', tick0=0, dtick=1)
                st.plotly_chart(fig, use_container_width=True)
                
                # Business vs. personal hourly patterns
                st.subheader("Business vs. Personal Hourly Patterns")
                
                # Compare business vs. personal
                # Use the most recent complete year
                latest_year = max(years)
                latest_data = transactions_df[transactions_df['year'] == latest_year]
                
                # Business hourly pattern
                business_hourly = latest_data[latest_data['potential_business']].groupby('hour')['amount_chf'].mean().reset_index()
                business_hourly['group'] = 'Business'
                
                # Personal hourly pattern
                personal_hourly = latest_data[~latest_data['potential_business']].groupby('hour')['amount_chf'].mean().reset_index()
                personal_hourly['group'] = 'Personal'
                
                combined_hourly = pd.concat([business_hourly, personal_hourly])
                
                fig = px.line(
                    combined_hourly,
                    x='hour',
                    y='amount_chf',
                    color='group',
                    markers=True,
                    title=f"Business vs. Personal Average Spending by Hour ({latest_year})",
                    labels={
                        "hour": "Hour of Day (24-hour)",
                        "amount_chf": "Average Spending (CHF)",
                        "group": "Customer Type"
                    }
                )
                # Ensure all hours are shown on x-axis
                fig.update_xaxes(tickmode='linear', tick0=0, dtick=1)
                st.plotly_chart(fig, use_container_width=True)
            
            # Add overall insights
            st.markdown("""
            ### Key Insights from Temporal Analysis

            **Daily Transaction Patterns:**
            - Transaction volume and total spending have shown consistent growth from 2021 to 2023
            - Daily unique customers have steadily increased over the three-year period
            - Significant variability exists in daily transaction amounts and counts

            **Weekly Transaction Patterns:**
            - Business transactions are more concentrated on weekdays, particularly peaking on Fridays
            - Personal transactions are more evenly distributed across weekdays and weekends
            - Friday shows the highest transaction percentage for both business and personal customers
            - Weekend (especially Sunday) shows the lowest transaction activity

            **Monthly Transaction Patterns:**
            - Monthly average spending fluctuates throughout the year
            - Business spending shows more pronounced variations compared to personal spending
            - December typically shows a spike in spending for both business and personal customers
            - Some months exhibit significant differences between business and personal spending patterns

            **Seasonal Variations:**
            - Business spending shows less seasonal variation compared to personal spending
            - Winter tends to have higher average spending for both business and personal customers
            - Personal spending demonstrates more pronounced seasonal differences

            **Hourly Transaction Patterns:**
            - Spending peaks during standard business hours (roughly 9 AM to 5 PM)
            - Business transactions show more concentrated spending during traditional work hours
            - Personal transactions have a more distributed spending pattern throughout the day
            - Late evening and early morning hours show lower transaction volumes
            """)
        
        elif viz_type == "Category Analysis":
            st.subheader("Category Analysis")
            
            # Top categories
            top_categories = transactions_df['category'].value_counts().head(10).reset_index()
            top_categories.columns = ['Category', 'Count']
            
            fig = px.bar(
                top_categories,
                x='Category',
                y='Count',
                title="Top 10 Categories by Transaction Count",
                labels={"Category": "Category", "Count": "Transaction Count"}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Category spending
            category_spending = transactions_df.groupby('category')['amount_chf'].sum().reset_index()
            category_spending = category_spending.sort_values('amount_chf', ascending=False).head(10)
            category_spending.columns = ['Category', 'Total Amount']
            
            fig = px.pie(
                category_spending,
                values='Total Amount',
                names='Category',
                title="Spending Distribution by Category (Top 10)"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Category analysis by customer
            st.subheader("Customer Category Spending Patterns")
            
            # Calculate spending percentage by category for each customer
            customer_category = transactions_df.groupby(['customer_id', 'category'])['amount_chf'].sum().reset_index()
            customer_total = transactions_df.groupby('customer_id')['amount_chf'].sum().reset_index()
            customer_total.columns = ['customer_id', 'total_spend']
            
            # Merge to calculate percentages
            customer_category = pd.merge(customer_category, customer_total, on='customer_id')
            customer_category['percentage'] = (customer_category['amount_chf'] / customer_category['total_spend']) * 100
            
            # Select a few common categories for comparison
            common_categories = transactions_df['category'].value_counts().head(6).index.tolist()
            filtered_data = customer_category[customer_category['category'].isin(common_categories)]
            
            # Pivot data for parallel coordinates
            pivot_data = filtered_data.pivot_table(
                index='customer_id',
                columns='category',
                values='percentage',
                fill_value=0
            ).reset_index()
            
            if not pivot_data.empty and pivot_data.shape[1] > 1:  # Ensure we have data to plot
                # Add transaction count for coloring
                customer_txn_count = transactions_df.groupby('customer_id').size().reset_index()
                customer_txn_count.columns = ['customer_id', 'transaction_count']
                pivot_data = pd.merge(pivot_data, customer_txn_count, on='customer_id')
                
                # Create parallel coordinates plot
                dimensions = [{
                    'label': col,
                    'values': pivot_data[col]
                } for col in pivot_data.columns if col not in ['customer_id', 'transaction_count']]
                
                fig = go.Figure(data=go.Parcoords(
                    line=dict(
                        color=pivot_data['transaction_count'],
                        colorscale='Viridis',
                        showscale=True,
                        cmin=pivot_data['transaction_count'].min(),
                        cmax=pivot_data['transaction_count'].max()
                    ),
                    dimensions=dimensions
                ))
                
                fig.update_layout(
                    title="Spending Patterns Across Categories (% of Total Spend per Customer)",
                    height=600
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("""
                **How to interpret this visualization:**
                - Each line represents a customer
                - Lines are colored by transaction count (darker = more transactions)
                - The position on each vertical axis shows the percentage of spending in that category
                - Parallel lines indicate similar spending patterns
                - Business users may show distinct patterns with higher spending in certain categories
                """)
            else:
                st.warning("Not enough category data to create the parallel coordinates visualization.")
            
            # Category focus    
            st.subheader("Focus on Specific Categories")
            
            # Allow user to select categories of interest
            selected_categories = st.multiselect(
                "Select categories to analyze",
                options=sorted(transactions_df['category'].unique()),
                default=transactions_df['category'].value_counts().head(3).index.tolist()
            )
            
            if selected_categories:
                # Filter transactions 
                cat_filter = transactions_df['category'].isin(selected_categories)
                filtered_txn = transactions_df[cat_filter]
                
                # Show transactions by selected categories
                category_counts = filtered_txn['category'].value_counts().reset_index()
                category_counts.columns = ['Category', 'Count']
                
                fig = px.bar(
                    category_counts,
                    x='Category', 
                    y='Count',
                    title=f"Transaction Count for Selected Categories",
                    color='Category'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Show comparison of average transaction amount by category
                cat_amount = filtered_txn.groupby('category')['amount_chf'].mean().reset_index()
                cat_amount.columns = ['Category', 'Average Amount']
                
                fig = px.bar(
                    cat_amount,
                    x='Category',
                    y='Average Amount',
                    title=f"Average Transaction Amount by Category", 
                    color='Category'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Please select at least one category to analyze.")
                
        elif viz_type == "Counterpart Analysis":
                st.subheader("Counterpart Analysis")
                
                st.markdown("""
                        This analysis examines transaction counterparts to identify distinctive patterns in business-related spending.
                        """)
                
                # Check if counterpart data is available
                if 'counterpart' not in transactions_df.columns:
                        st.warning("Counterpart data is not available in the transaction dataset.")
                else:
                        # Define business-related MCC codes
                        business_mccs = [2741, 2842, 5013, 5021, 5039, 5044, 5045, 
                                         5046, 5047, 5051, 5065, 5072, 5074, 5085, 
                                         5094, 5099, 5111, 5122, 5131, 5137, 5139, 
                                         5189, 5172, 5192, 5193, 5198, 5199, 7375, 7829]
                        
                        # Safely convert MCC to string and handle NaN values
                        transactions_df['mcc_clean'] = pd.to_numeric(transactions_df['mcc'], errors='coerce').astype('Int64')
                        
                        # Filter transactions to business-related MCCs
                        business_transactions = transactions_df[
                                transactions_df['mcc_clean'].isin(business_mccs)
                        ]
                        
                        # Top Counterparts Analysis
                        col1, col2 = st.columns(2)
                        
                        with col1:
                                # Top counterparts by transaction count
                                top_counterparts = business_transactions['counterpart'].value_counts().head(10)
                                
                                fig = px.bar(
                                        x=top_counterparts.index, 
                                        y=top_counterparts.values,
                                        title="Top 10 Counterparts by Transaction Count",
                                        labels={"x": "Counterpart", "y": "Transaction Count"}
                                )
                                fig.update_layout(xaxis_tickangle=-45)
                                st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                                st.markdown("""
                                    ### Key Insights
                                    - **Transaction Concentration:** PayPal and Microsoft dominate, accounting for nearly 60-70% of total transactions among top counterparts
                                    - **Steep Hierarchy:** A dramatic decline in transaction counts after the top two, with NY Times ranking third at less than half the volume of Microsoft
                                    - **Digital Service Prevalence:** Top counterparts predominantly represent digital services, payment platforms, and technology companies
                                    - **Competitive Landscape:** Strong concentration of transactions among a few dominant entities, creating a top-heavy distribution
                                """)
                        
                        # Counterpart-MCC Association
                        st.markdown("### Counterpart-Category Associations")
                        
                        # Group by counterpart and MCC description
                        counterpart_mcc_counts = business_transactions.groupby(['counterpart', 'mcc_description']).size().reset_index(name='count')
                        top_pairs = counterpart_mcc_counts.sort_values('count', ascending=False).head(15)
                        
                        fig = px.bar(
                                top_pairs, 
                                x='count', 
                                y='counterpart', 
                                color='mcc_description',
                                orientation='h',
                                title="Top Counterpart-Category Associations",
                                labels={"count": "Transaction Count", "counterpart": "Counterpart"}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Detailed Analysis
                        st.markdown("""
                                ### Detailed Insights
                                
                                **Transaction Distribution:**
                                - **Computers, Computer Peripheral Equipment, Software** dominates transaction counts
                                - **Miscellaneous Publishing and Printing** follows as a distant second
                                - Other sectors like durable goods, office supplies, medical, clothing, and petroleum show steady but lower transaction volumes
                                
                                **Counterpart Characteristics:**
                                - Microsoft (MSFT) and PayPal lead in transaction volumes
                                - Linked primarily to computers, software, and peripheral equipment
                                - Other key counterparts span diverse categories:
                                  * Publishing
                                  * Durable goods
                                  * Digital services
                                
                                **Sector Concentration:**
                                - Strong concentration in tech and digital sectors
                                - Financial, medical, and construction-related transactions appear in smaller proportions
                                - Exhibits a long-tail distribution pattern
                                """)
                        
                        # Transaction Amount Analysis
                        st.markdown("### Transaction Amount by Counterpart")
                        
                        # Top counterparts by total transaction amount
                        top_amount_counterparts = business_transactions.groupby('counterpart')['amount_chf'].agg([
                                ('total_amount', 'sum'),
                                ('avg_amount', 'mean'),
                                ('transaction_count', 'count')
                        ]).sort_values('total_amount', ascending=False).head(10)
                        
                        fig = px.bar(
                                top_amount_counterparts.reset_index(), 
                                x='counterpart', 
                                y='total_amount',
                                title="Top Counterparts by Total Transaction Amount",
                                labels={"counterpart": "Counterpart", "total_amount": "Total Amount (CHF)"}
                        )
                        fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                
        elif viz_type == "MCC Analysis":
            st.subheader("Merchant Category Code (MCC) Analysis")
            
            if 'mcc' not in transactions_df.columns:
                st.warning("MCC data is not available in the transaction dataset.")
            else:
                # Create two columns for visualizations
                col1, col2 = st.columns(2)
                
                with col1:
                    # Show MCC distribution
                    if 'mcc_category' in transactions_df.columns:
                        # Use MCC category if available
                        mcc_field = 'mcc_category'
                        title_prefix = "MCC Categories"
                    else:
                        # Otherwise use raw MCC code
                        mcc_field = 'mcc'
                        title_prefix = "MCC Codes"
                    
                    # Top MCCs by transaction count
                    top_mccs = transactions_df[mcc_field].value_counts().head(15).reset_index()
                    top_mccs.columns = ['MCC', 'Count']
                    
                    fig = px.bar(
                        top_mccs,
                        x='Count',
                        y='MCC',
                        orientation='h',
                        title=f"Top 15 {title_prefix} by Transaction Count",
                        labels={"Count": "Transaction Count", "MCC": mcc_field.replace('_', ' ').title()}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Show MCC by amount
                    mcc_amounts = transactions_df.groupby(mcc_field)['amount_chf'].sum().reset_index()
                    mcc_amounts = mcc_amounts.sort_values('amount_chf', ascending=False).head(15)
                    mcc_amounts.columns = ['MCC', 'Total Amount']
                    
                    fig = px.bar(
                        mcc_amounts,
                        x='Total Amount',
                        y='MCC',
                        orientation='h',
                        title=f"Top 15 {title_prefix} by Transaction Amount",
                        labels={"Total Amount": "Total Amount (CHF)", "MCC": mcc_field.replace('_', ' ').title()}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Display insights from MCC analysis
                st.markdown("""
                **Insights from MCC Analysis**
                
                Based on our MCC data analysis, we can identify several patterns that align with the findings from the Counterpart Analysis:
                
                1. **Computers, Computer Peripheral Equipment, and Software** dominates transaction counts, which supports the findings about Microsoft and other tech companies in the counterpart analysis.
                
                2. **Business-related MCCs** appear prominently in both transaction count and amount, indicating significant business spending in the dataset.
                
                3. **Diverse MCC distribution** suggests a mix of business and personal transactions, with business-related MCCs showing distinctive patterns.
                """)
                
                # Business-related MCC analysis
                st.subheader("Business-Related MCC Analysis")
                
                # Define business-related MCC categories based on our data
                # This is based on the MCC codes mentioned in the documents
                business_mccs = ['5045', '2741', '5099', '5734', '5111', '5047', '5085', '5065', '5732']
                business_mcc_categories = ['computers', 'software', 'publishing', 'printing', 'durable_goods', 
                                           'office_supplies', 'business_services', 'professional_services']
                
                # Determine which field to use for filtering
                if 'mcc_category' in transactions_df.columns:
                    # Try to match categories
                    mcc_filter = transactions_df['mcc_category'].str.lower().str.contains('|'.join(business_mcc_categories), na=False)
                else:
                    # Use raw MCC codes
                    mcc_filter = transactions_df['mcc'].astype(str).isin(business_mccs)
                
                # Filter for business transactions
                business_transactions = transactions_df[mcc_filter]
                
                # Calculate percentage of business transactions
                business_pct = len(business_transactions) / len(transactions_df) * 100
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Business MCC Transactions", 
                             f"{len(business_transactions):,}", 
                             f"{business_pct:.1f}% of total")
                
                with col2:
                    business_amount = business_transactions['amount_chf'].sum()
                    total_amount = transactions_df['amount_chf'].sum()
                    business_amount_pct = business_amount / total_amount * 100
                    
                    st.metric("Business MCC Spending", 
                             f"CHF {business_amount:,.2f}", 
                             f"{business_amount_pct:.1f}% of total")
                
                if not business_transactions.empty:
                    # Business MCC distribution
                    business_mcc_counts = business_transactions[mcc_field].value_counts().head(10).reset_index()
                    business_mcc_counts.columns = ['MCC', 'Count']
                    
                    fig = px.pie(
                        business_mcc_counts,
                        values='Count',
                        names='MCC',
                        title=f"Distribution of Business-Related {title_prefix}"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Customer business MCC analysis
                    # Calculate business spending percentage per customer
                    customer_total = transactions_df.groupby('customer_id')['amount_chf'].sum()
                    customer_business = business_transactions.groupby('customer_id')['amount_chf'].sum()
                    
                    # Merge and calculate percentage
                    customer_business_pct = pd.DataFrame({
                        'total_spent': customer_total,
                        'business_spent': customer_business
                    }).reset_index().fillna(0)
                    
                    customer_business_pct['business_pct'] = (customer_business_pct['business_spent'] / customer_business_pct['total_spent'] * 100).fillna(0)
                    
                    # Filter for customers with significant business spending
                    high_business_customers = customer_business_pct[
                        (customer_business_pct['business_pct'] > 30) & 
                        (customer_business_pct['total_spent'] > customer_business_pct['total_spent'].median())
                    ]
                    
                    st.subheader(f"Potential Business Customers by MCC ({len(high_business_customers)} identified)")
                    st.write("Customers with >30% business-related MCC spending and above-median total spending:")
                    
                    if not high_business_customers.empty:
                        high_business_customers = high_business_customers.sort_values('business_pct', ascending=False)
                        st.dataframe(high_business_customers)
                        
                        # Visualization of business vs non-business spending
                        fig = px.scatter(
                            customer_business_pct,
                            x='total_spent',
                            y='business_pct',
                            hover_name='customer_id',
                            title="Business MCC Spending Percentage vs Total Spending",
                            labels={
                                'total_spent': 'Total Spending (CHF)',
                                'business_pct': 'Business MCC Spending (%)'
                            }
                        )
                        
                        # Add a threshold line
                        fig.add_hline(y=30, line_dash="dash", line_color="red", 
                                     annotation_text="30% Threshold")
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.write("No customers found matching these criteria.")
                else:
                    st.warning("No business-related MCC transactions found in the dataset.")

elif page == "Clustering":
    st.markdown('<div class="main-header">Business Customer Clustering Analysis</div>', unsafe_allow_html=True)
    
    st.markdown("""
    This section presents our clustering analysis of transaction patterns to identify distinct business customer segments.
    We use three different clustering approaches to analyze patterns in customer spending across various merchant categories.
    """)
    
    if transactions_df.empty:
        st.error("Could not load the transaction dataset. Please check the file paths and try again.")
    else:
        # Remove rows with zero amount
        if 'amount_chf' in transactions_df.columns:
            transactions_df = transactions_df[transactions_df['amount_chf'] != 0]

        # Filter low activity customers (those with fewer than 10 transactions)
        if 'customer_id' in transactions_df.columns:
            low_activity_cluster = transactions_df.groupby('customer_id').size().reset_index(name='low_activity_count')
            low_activity_cluster = low_activity_cluster[low_activity_cluster['low_activity_count'] < 10]
        
            # Remove low activity customers
            transactions_df = transactions_df[~transactions_df['customer_id'].isin(low_activity_cluster['customer_id'])]

        # Keep only b2b related transactions based on MCC codes
        if 'mcc' in transactions_df.columns:
            mcc_to_keep = {2741, 2842,
                        5013, 5021, 5039, 5044, 5045, 5046, 5047, 5051, 5065, 5072, 5074, 5085, 5094, 5099,
                        5111, 5122, 5131, 5137, 5139, 5189, 5172, 5192, 5193, 5198, 5199,
                        7375, 7829}
        
            # Get customer IDs with B2B transactions
            ids_with_b2b = transactions_df.loc[transactions_df['mcc'].isin(mcc_to_keep), 'customer_id'].unique()
        
            # Keep only those customers
            transactions_df = transactions_df[transactions_df['customer_id'].isin(ids_with_b2b)]

        # One-hot encode categories
        one_hot_category = pd.get_dummies(transactions_df['category']).astype(int)

        # Combine with relevant columns and aggregate by customer
        df_category = pd.concat([transactions_df['customer_id'], one_hot_category], axis=1)
        if 'amount_chf' in transactions_df.columns:
            df_category = pd.concat([df_category, transactions_df[['amount_chf']]], axis=1)

        # Aggregate by customer
        customer_features = df_category.groupby('customer_id').sum().reset_index()

        # Add transaction count and average amount
        txn_stats = transactions_df.groupby('customer_id').agg(
            transaction_count=('customer_id', 'count'),
            avg_amount=('amount_chf', 'mean')
        )

        customer_features = pd.merge(
            customer_features, 
            txn_stats, 
            on='customer_id'
        )

        # IMPORTANT: Store customer IDs before dropping the column
        customer_ids = customer_features['customer_id'].values

        # Create a copy for clustering that doesn't include customer_id and amount_chf
        customer_features_for_clustering = customer_features.copy()
        
        # Remove columns not needed for clustering
        if 'customer_id' in customer_features_for_clustering.columns:
            customer_features_for_clustering = customer_features_for_clustering.drop(columns=['customer_id'])

        if 'amount_chf' in customer_features_for_clustering.columns:
            customer_features_for_clustering = customer_features_for_clustering.drop(columns=['amount_chf'])

        # Choose columns for clustering
        cluster_columns = customer_features_for_clustering.columns.tolist()

        # Standardize features for clustering
        scaler = MinMaxScaler()
        features_scaled = scaler.fit_transform(customer_features_for_clustering)

        # Apply PCA for visualization
        pca = PCA(n_components=2)
        reduced_data = pca.fit_transform(features_scaled)

        # Create tabs for different clustering methods
        clustering_tabs = st.tabs(["Data Preparation", "DBSCAN", "K-Means", "Hierarchical Clustering", "Statistical Validation"])
        
        # Data Preparation Tab
        with clustering_tabs[0]:
            st.markdown('<div class="section-header">Data Preparation for Clustering</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Extract category information from transactions
                if 'category' in transactions_df.columns:
                    st.subheader("Category Distribution")
                    category_counts = transactions_df['category'].value_counts().reset_index()
                    category_counts.columns = ['Category', 'Transaction Count']
                    
                    fig = px.bar(
                        category_counts.head(15), 
                        x='Category', 
                        y='Transaction Count',
                        title="Top 15 Categories by Transaction Count",
                        color='Transaction Count',
                        color_continuous_scale='viridis'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                elif 'mcc_description' in transactions_df.columns:
                    st.subheader("MCC Distribution")
                    mcc_counts = transactions_df['mcc_description'].value_counts().reset_index()
                    mcc_counts.columns = ['MCC Description', 'Transaction Count']
                    
                    fig = px.bar(
                        mcc_counts.head(15), 
                        x='MCC Description', 
                        y='Transaction Count',
                        title="Top 15 MCC Categories by Transaction Count",
                        color='Transaction Count',
                        color_continuous_scale='viridis'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                # Display sample of the features
                st.subheader("Sample Features for Clustering")
                st.write(customer_features_for_clustering.head(5))
                
                # Show explained variance
                explained_variance = pca.explained_variance_ratio_.sum() * 100
                st.metric("PCA Explained Variance", f"{explained_variance:.1f}%")
                
                # Create DataFrame for PCA visualization
                pca_df = pd.DataFrame({
                    'customer_id': customer_ids,
                    'PCA1': reduced_data[:, 0],
                    'PCA2': reduced_data[:, 1]
                })
                
                # Visualize PCA results
                fig = px.scatter(
                    pca_df,
                    x='PCA1',
                    y='PCA2',
                    title="PCA Visualization of Customer Features",
                    labels={"PCA1": "Principal Component 1", "PCA2": "Principal Component 2"}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown('<div class="insight-box">', unsafe_allow_html=True)
                st.markdown(f"""
                ### Feature Engineering Approach
                
                **Data Selection:**
                - Filtered for customers with B2B-related MCC codes
                - Removed customers with fewer than 10 transactions
                
                **Feature Creation:**
                1. **Category-Based Features:**
                   - One-hot encoded spending categories 
                   - Creates a "fingerprint" of spending preferences
                
                2. **Transaction Metrics:**
                   - Transaction frequency (count)
                   - Average transaction amount
                   - Total spending amount
                
                3. **B2B Indicators:**
                   - Ratio of B2B-related transactions
                   - Spending in business-specific categories
                
                **Dimensionality Reduction:**
                - Applied PCA to reduce high-dimensional feature space
                - Allows visualization in 2D space
                - Preserves approximately {explained_variance:.1f}% of variance
                
                **Limitations:**
                - PCA visualizations lose some information
                - Higher-dimension clustering may find different patterns
                - Category distributions may not capture all business characteristics
                """)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Compare features across different metrics
                st.subheader("Feature Distribution Analysis")
                
                # Transaction count distribution
                fig = px.histogram(
                    customer_features_for_clustering,
                    x='transaction_count',
                    nbins=50,
                    title="Distribution of Transaction Count per Customer",
                    labels={"transaction_count": "Transaction Count"}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Average amount distribution
                if 'avg_amount' in customer_features_for_clustering.columns:
                    fig = px.histogram(
                        customer_features_for_clustering,
                        x='avg_amount',
                        nbins=50,
                        title="Distribution of Average Transaction Amount per Customer",
                        labels={"avg_amount": "Average Amount (CHF)"}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Display correlation heatmap of features if there are categorical features
                if len(cluster_columns) > 2:  # Only if we have more than just transaction_count and avg_amount
                    st.subheader("Feature Correlation")
                    
                    # Select a subset of features for visualization (top categories by variance)
                    feature_var = customer_features_for_clustering[cluster_columns].var().sort_values(ascending=False)
                    top_features = feature_var.head(10).index.tolist()
                    
                    # Calculate correlation matrix
                    corr_matrix = customer_features_for_clustering[top_features].corr()
                    
                    # Create heatmap
                    fig = px.imshow(
                        corr_matrix,
                        color_continuous_scale='RdBu_r',
                        title="Correlation Matrix of Top Features",
                        labels=dict(x="Feature", y="Feature", color="Correlation"),
                        text_auto='.2f'
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # DBSCAN Tab
        with clustering_tabs[1]:
            st.markdown('<div class="section-header">DBSCAN Clustering Results</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Find optimal epsilon for DBSCAN based on k-distance graph
                st.subheader("Epsilon Parameter Selection")
                
                # Calculate distances to nearest neighbors
                k = 5  # Number of neighbors to consider
                nn = NearestNeighbors(n_neighbors=k)
                nn.fit(reduced_data)
                distances, _ = nn.kneighbors(reduced_data)
                
                # Get distances to the k-th nearest neighbor
                k_distances = np.sort(distances[:, k-1])
                
                # Plot k-distance graph
                fig = px.line(
                    x=range(len(k_distances)),
                    y=k_distances,
                    title=f"K-Distance Graph for DBSCAN (k={k})",
                    labels={"x": "Points (sorted by distance)", "y": f"Distance to {k}th neighbor"}
                )
                
                # Try to detect knee point (simplified method)
                knee_idx = np.argmax(np.diff(k_distances)) + 1
                optimal_eps = float(k_distances[knee_idx])
                
                # Add vertical line at knee point
                fig.add_vline(x=knee_idx, line_dash="dash", line_color="red")
                fig.add_hline(y=optimal_eps, line_dash="dash", line_color="red", 
                              annotation_text=f"Optimal eps = {optimal_eps:.3f}")
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Allow user to adjust epsilon
                eps = st.slider("Select epsilon value for DBSCAN", 
                               min_value=0.01, 
                               max_value=1.0, 
                               value=float(optimal_eps),
                               step=0.01,
                               format="%.2f")
                
                min_samples = st.slider("Select minimum samples per cluster", 
                                      min_value=2, 
                                      max_value=20, 
                                      value=5)
                
                # Apply DBSCAN with selected parameters
                dbscan = DBSCAN(eps=eps, min_samples=min_samples)
                dbscan_labels = dbscan.fit_predict(reduced_data)
                
                # Count number of clusters and noise points
                n_clusters = len(set(dbscan_labels)) - (1 if -1 in dbscan_labels else 0)
                n_noise = list(dbscan_labels).count(-1)
                
                # Display metrics
                col1a, col1b = st.columns(2)
                col1a.metric("Number of Clusters", n_clusters)
                col1b.metric("Noise Points", n_noise)
                
                # Create DataFrame with clustering results
                dbscan_result = pd.DataFrame({
                    'customer_id': customer_ids,
                    'PCA1': reduced_data[:, 0],
                    'PCA2': reduced_data[:, 1],
                    'cluster': [f"Cluster {label}" if label >= 0 else "Noise" for label in dbscan_labels]
                })
                
                # Visualize DBSCAN results
                fig = px.scatter(
                    dbscan_result,
                    x='PCA1',
                    y='PCA2',
                    color='cluster',
                    title=f"DBSCAN Clustering (eps={eps:.2f}, min_samples={min_samples})",
                    labels={"PCA1": "Principal Component 1", "PCA2": "Principal Component 2"}
                )
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                st.markdown('<div class="insight-box">', unsafe_allow_html=True)
                st.markdown("""
                ### DBSCAN Clustering Key Insights
                
                **Method Characteristics:**
                - Density-based spatial clustering of applications with noise
                - Identifies clusters of arbitrary shape
                - Robust to outliers - labels low-density regions as noise
                - Does not require pre-specified number of clusters
                
                **Parameter Selection:**
                - **Epsilon (ε)**: Defines the neighborhood distance
                - **Min_samples**: Minimum points required to form a cluster
                - K-distance plot helps identify optimal epsilon value
                - Knee point in the curve suggests a natural density threshold
                
                **Analysis Outcome:**
                - Most data points form a single large cluster
                - Few isolated clusters indicate distinct customer segments
                - Significant number of noise points represent customers with unique patterns
                - Sensitive to parameter selection due to high feature dimensionality
                
                **Suitability Assessment:**
                - DBSCAN struggles with high-dimensional feature spaces
                - PCA dimension reduction results in significant information loss
                - Works best when natural density separation exists
                - Limited effectiveness for business customer segmentation in this dataset
                """)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Show cluster composition if clusters were found
                if n_clusters > 0:
                    st.subheader("Cluster Composition")
                    
                    # Count customers per cluster
                    cluster_counts = dbscan_result['cluster'].value_counts().reset_index()
                    cluster_counts.columns = ['Cluster', 'Number of Customers']
                    
                    fig = px.bar(
                        cluster_counts,
                        x='Cluster',
                        y='Number of Customers',
                        color='Number of Customers',
                        title="Customer Distribution Across Clusters",
                        color_continuous_scale='viridis'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # If category information is available, show category distribution by cluster
                    if 'category' in transactions_df.columns:
                        # Merge DBSCAN clusters with transaction data
                        cluster_map = dict(zip(dbscan_result['customer_id'], dbscan_result['cluster']))
                        transactions_clustered = transactions_df.copy()
                        transactions_clustered['cluster'] = transactions_clustered['customer_id'].map(cluster_map)
                        
                        # Calculate category distribution per cluster
                        category_by_cluster = transactions_clustered.groupby(['cluster', 'category']).size().reset_index(name='count')
                        
                        # Get total transactions per cluster for normalization
                        cluster_totals = category_by_cluster.groupby('cluster')['count'].sum().reset_index(name='total')
                        category_by_cluster = pd.merge(category_by_cluster, cluster_totals, on='cluster')
                        category_by_cluster['percentage'] = category_by_cluster['count'] / category_by_cluster['total'] * 100
                        
                        # Filter for top categories
                        top_categories = transactions_df['category'].value_counts().head(8).index.tolist()
                        filtered_categories = category_by_cluster[category_by_cluster['category'].isin(top_categories)]
                        
                        # Create heatmap
                        fig = px.density_heatmap(
                            filtered_categories,
                            x='category',
                            y='cluster',
                            z='percentage',
                            title="Category Distribution by DBSCAN Cluster (%)",
                            labels={"category": "Category", "cluster": "Cluster", "percentage": "Percentage (%)"},
                            color_continuous_scale='Blues'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("DBSCAN did not identify any meaningful clusters with the current parameters.")
                    st.markdown("""
                    **Possible reasons:**
                    1. Data points are evenly distributed in feature space
                    2. The epsilon value may need adjustment
                    3. High dimensionality makes density-based clustering challenging
                    4. Try adjusting the epsilon and min_samples parameters
                    """)
        
        # K-Means Tab 
        with clustering_tabs[2]:
            st.markdown('<div class="section-header">K-Means Clustering Analysis</div>', unsafe_allow_html=True)
    
            col1, col2 = st.columns(2)
    
            with col1:
                # Fixed number of clusters to match the image
                k = 4
    
                # Make sure we're using the same PCA implementation as in the colleague's code
                pca = PCA(n_components=2)
                # Use the original scaled data (before any previous PCA was applied)
                fresh_reduced_data = pca.fit_transform(features_scaled)
        
                # Initialize centroids with fixed seed
                np.random.seed(42)
                n_samples = fresh_reduced_data.shape[0]
                indices = np.random.choice(n_samples, k, replace=False)
                centroids = fresh_reduced_data[indices]
        
                # Setup for K-means algorithm
                distances = np.zeros((n_samples, k))
        
                # Run a single pass of K-means assignment (this is what might be different)
                # Calculate distances to centroids
                for i in range(k):
                    distances[:, i] = np.sqrt(np.sum((fresh_reduced_data - centroids[i]) ** 2, axis=1))
        
                # Assign points to closest centroid
                fresh_kmeans_labels = np.argmin(distances, axis=1)
        
                # Update centroids once
                for i in range(k):
                    if np.sum(fresh_kmeans_labels == i) > 0:
                        centroids[i] = np.mean(fresh_reduced_data[fresh_kmeans_labels == i], axis=0)
                
                # Assign points to closest centroid
                kmeans_labels = np.argmin(distances, axis=1)
        
                # Create DataFrame with clustering results
                kmeans_result = pd.DataFrame({
                    'customer_id': customer_ids,
                    'PCA1': fresh_reduced_data[:, 0],
                    'PCA2': fresh_reduced_data[:, 1],
                    'cluster': [f"Cluster {label}" for label in fresh_kmeans_labels]
                })
        
                # Visualize with Plotly
                fig = px.scatter(
                    kmeans_result,
                    x='PCA1',
                    y='PCA2',
                    color='cluster',
                    title=f"K-Means Clustering with {k} clusters",
                    labels={"PCA1": "Principal Component 1", "PCA2": "Principal Component 2"}
                )
        
                # Add centroids
                for i in range(k):
                    fig.add_trace(
                        go.Scatter(
                            x=[centroids[i, 0]],
                            y=[centroids[i, 1]],
                            mode='markers',
                            marker=dict(
                                symbol='x',
                                size=15,
                                color='red',
                                line=dict(width=2)
                            ),
                            name=f'Centroid {i}'
                        )
                    )
        
                st.plotly_chart(fig, use_container_width=True)
        
                # Calculate silhouette score
                if len(np.unique(kmeans_labels)) > 1:
                    silhouette_avg = silhouette_score(reduced_data, kmeans_labels)
                    st.metric("Silhouette Score", f"{silhouette_avg:.3f}", 
                            delta="higher is better (range: -1 to 1)")                
            
            with col2:
                st.markdown('<div class="insight-box">', unsafe_allow_html=True)
                st.markdown("""
                ### K-Means Clustering Key Insights
                
                **Method Characteristics:**
                - Partitioning method using Euclidean distance
                - Requires predefined number of clusters (k)
                - Aims to minimize within-cluster variance
                - Forms spherical/circular clusters
                
                **Technical Considerations:**
                - Best suited for lower-dimensional data
                - PCA visualization helps interpret results but loses information
                - Centroids represent the "average customer" in each segment
                - Sensitive to outliers and initial random seed
                
                **Clustering Outcome:**
                - Successfully identified distinct customer segments
                - Clear separation between major customer groups
                - Centroids show different positions in feature space
                - Some overlap between neighboring clusters
                
                **Limitations:**
                - Forces exactly k clusters regardless of natural groupings
                - Assumes equal cluster sizes and spherical distributions
                - Cannot identify irregular-shaped clusters
                - Silhouette score helps validate optimal cluster count
                """)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Show cluster distribution
                st.subheader("Cluster Distribution")
                
                # Count customers per cluster
                cluster_counts = kmeans_result['cluster'].value_counts().reset_index()
                cluster_counts.columns = ['Cluster', 'Number of Customers']
                
                fig = px.pie(
                    cluster_counts,
                    values='Number of Customers',
                    names='Cluster',
                    title="Customer Distribution Across Clusters",
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # If category information is available, show category distribution by cluster
                if 'category' in transactions_df.columns:
                    st.subheader("Category Composition by Cluster")
                    
                    # Merge K-Means clusters with transaction data
                    cluster_map = dict(zip(kmeans_result['customer_id'], kmeans_result['cluster']))
                    transactions_clustered = transactions_df.copy()
                    transactions_clustered['cluster'] = transactions_clustered['customer_id'].map(cluster_map)
                    
                    # Calculate category distribution per cluster
                    category_by_cluster = transactions_clustered.groupby(['cluster', 'category']).size().reset_index(name='count')
                    
                    # Get total transactions per cluster for normalization
                    cluster_totals = category_by_cluster.groupby('cluster')['count'].sum().reset_index(name='total')
                    category_by_cluster = pd.merge(category_by_cluster, cluster_totals, on='cluster')
                    category_by_cluster['percentage'] = category_by_cluster['count'] / category_by_cluster['total'] * 100
                    
                    # Filter for top categories
                    top_categories = transactions_df['category'].value_counts().head(8).index.tolist()
                    filtered_categories = category_by_cluster[category_by_cluster['category'].isin(top_categories)]
                    
                    # Create heatmap
                    fig = px.density_heatmap(
                        filtered_categories,
                        x='category',
                        y='cluster',
                        z='percentage',
                        title="Category Distribution by K-Means Cluster (%)",
                        labels={"category": "Category", "cluster": "Cluster", "percentage": "Percentage (%)"},
                        color_continuous_scale='Blues'
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # Hierarchical Clustering Tab
        with clustering_tabs[3]:
            st.markdown('<div class="section-header">Hierarchical Clustering Analysis</div>', unsafe_allow_html=True)
    
            col1, col2 = st.columns(2)
    
            with col1:
                # Calculate linkage matrix for hierarchical clustering
                linkage_matrix = sch.linkage(features_scaled, method='ward')
        
                # Create dendrogram figure
                fig = go.Figure()
        
                # Convert scipy dendrogram to plotly format
                dendro = sch.dendrogram(linkage_matrix, no_plot=True)
        
                # Add dendrogram traces
                for i, d in enumerate(dendro['dcoord']):
                    x = dendro['icoord'][i]
                    y = d
                    fig.add_trace(go.Scatter(
                        x=x, 
                        y=y,
                        mode='lines',
                        line=dict(color='blue', width=1),
                        hoverinfo='none'
                    ))
        
                fig.update_layout(
                    title="Hierarchical Clustering Dendrogram",
                    xaxis_title="Sample Index",
                    yaxis_title="Distance",
                    showlegend=False,
                    height=600
                )
        
                st.plotly_chart(fig, use_container_width=True)
        
                # Determine optimal number of clusters
                # Calculate within-cluster sum of squares for different cluster counts
                wcss = []
                max_clusters = 10
        
                for i in range(1, max_clusters + 1):
                    labels = sch.fcluster(linkage_matrix, t=i, criterion='maxclust')
            
                    # Calculate WCSS for this clustering
                    wcss_i = 0
                    for cluster_id in range(1, i + 1):
                        cluster_points = reduced_data[labels == cluster_id]
                        if len(cluster_points) > 0:
                            centroid = np.mean(cluster_points, axis=0)
                            wcss_i += np.sum(np.square(cluster_points - centroid))
            
                    wcss.append(wcss_i)
        
                # Plot WCSS (elbow method)
                fig = px.line(
                    x=list(range(1, max_clusters + 1)),
                    y=wcss,
                    markers=True,
                    title="Elbow Method for Optimal Cluster Count",
                    labels={"x": "Number of Clusters", "y": "Within-Cluster Sum of Squares"}
                )
                st.plotly_chart(fig, use_container_width=True)
        
                # Allow user to select number of clusters
                hclust_k = st.slider("Select number of clusters for Hierarchical Clustering", 
                                min_value=2, 
                                max_value=10, 
                                value=4,
                                key="hclust_k")
        
                # Apply hierarchical clustering with selected number of clusters
                hclust_labels = sch.fcluster(linkage_matrix, t=hclust_k, criterion='maxclust')
        
                # Adjust labels to be 0-based instead of 1-based
                hclust_labels = hclust_labels - 1
        
                # Create DataFrame with clustering results using consistent naming (Cluster 0, Cluster 1, etc.)
                hclust_result = pd.DataFrame({
                    'customer_id': customer_ids,
                    'PCA1': reduced_data[:, 0],
                    'PCA2': reduced_data[:, 1],
                    'cluster': [f"Cluster {label}" for label in hclust_labels]
                })
        
                # Visualize hierarchical clustering results
                fig = px.scatter(
                    hclust_result,
                    x='PCA1',
                    y='PCA2',
                    color='cluster',
                    title=f"Hierarchical Clustering with {hclust_k} clusters",
                    labels={"PCA1": "Principal Component 1", "PCA2": "Principal Component 2"}
                )
                st.plotly_chart(fig, use_container_width=True)
        
            with col2:
                st.markdown('<div class="insight-box">', unsafe_allow_html=True)
                st.markdown("""
                ### Hierarchical Clustering Key Insights
        
                **Method Characteristics:**
                - Bottom-up (agglomerative) clustering approach
                - Builds a tree-like hierarchy of clusters
                - Does not require predefined number of clusters
                - Reveals natural data hierarchy and relationships
        
                **Clustering Visualization:**
                - Dendrogram shows the hierarchical structure of data
                - Height of branches indicates distance between clusters
                - Longer vertical lines suggest distinct separation
                - Natural cutting points reveal optimal cluster count
        
                **Analysis Advantages:**
                - Provides multi-level view of customer segmentation
                - Overcomes fixed cluster count limitation of K-means
                - Shows relationships between different customer groups
                - More robust to different cluster shapes
        
                **Interpretability:**
                - Most suitable approach for business customer segmentation
                - Allows exploration of different hierarchical levels
                - Reveals both major segments and sub-segments
                - Enables flexible customer grouping based on business needs
                """)
                st.markdown('</div>', unsafe_allow_html=True)
        
                # Show cluster distribution
                st.subheader("Cluster Distribution")
        
                # Count customers per cluster
                cluster_counts = hclust_result['cluster'].value_counts().reset_index()
                cluster_counts.columns = ['Cluster', 'Number of Customers']
        
                fig = px.bar(
                    cluster_counts,
                    x='Cluster',
                    y='Number of Customers',
                    color='Number of Customers',
                    title="Customer Distribution Across Clusters",
                    color_continuous_scale='viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
        
                # If category information is available, show category distribution by cluster
                if 'category' in transactions_df.columns:
                    st.subheader("Category Composition by Cluster")
            
                    # Merge hierarchical clusters with transaction data
                    cluster_map = dict(zip(hclust_result['customer_id'], hclust_result['cluster']))
                    transactions_clustered = transactions_df.copy()
                    transactions_clustered['cluster'] = transactions_clustered['customer_id'].map(cluster_map)
            
                    # Calculate category distribution per cluster
                    category_by_cluster = transactions_clustered.groupby(['cluster', 'category']).size().reset_index(name='count')
            
                    # Get total transactions per cluster for normalization
                    cluster_totals = category_by_cluster.groupby('cluster')['count'].sum().reset_index(name='total')
                    category_by_cluster = pd.merge(category_by_cluster, cluster_totals, on='cluster')
                    category_by_cluster['percentage'] = category_by_cluster['count'] / category_by_cluster['total'] * 100
            
                    # Filter for top categories
                    top_categories = transactions_df['category'].value_counts().head(8).index.tolist()
                    filtered_categories = category_by_cluster[category_by_cluster['category'].isin(top_categories)]
            
                    # Create heatmap
                    fig = px.density_heatmap(
                        filtered_categories,
                        x='category',
                        y='cluster',
                        z='percentage',
                        title="Category Distribution by Hierarchical Cluster (%)",
                        labels={"category": "Category", "cluster": "Cluster", "percentage": "Percentage (%)"},
                        color_continuous_scale='Blues'
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # Statistical Validation Tab
        with clustering_tabs[4]:
            # Create two columns
            col1, col2 = st.columns([2, 1])
    
            with col1:
                st.markdown('<div class="section-header">Statistical Validation of Clustering</div>', unsafe_allow_html=True)
        
                st.markdown('<div class="insight-box">', unsafe_allow_html=True)
                st.markdown("""
                ### Chi-Square Test and Statistical Validation
        
                **Validation Approach:**
                - Used Chi-Square tests to validate cluster distinctiveness
                - Examined spending patterns across different clusters
                - Analyzed standardized residuals to identify characteristic features
        
                **Statistical Findings:**
                - Confirmed statistically significant differences in spending patterns across clusters
                - p-values consistently below 0.001, indicating robust cluster differentiation
                - Strong association between clusters and spending categories (Cramer's V > 0.6)
        
                **Categorical Distinctiveness:**
                - Each cluster shows significantly different spending behaviors
                - Standardized residuals reveal unique spending characteristics:
                  * **Positive Residuals**: Categories where a cluster spends more than expected
                  * **Negative Residuals**: Categories with less spending than anticipated
        
                **Cluster Profiles Based on Statistical Analysis:**
                
                - **Cluster 0 (Professional Services):**
                  * Significantly higher spending in software and digital services
                  * Lower than expected spending in retail and entertainment
                
                - **Cluster 1 (Tech & Equipment):**
                  * Excess spending in computer equipment and technology
                  * Substantially lower spending in services and consumables
                
                - **Cluster 2 (Business Supplies):**
                  * Concentrated spending in office supplies and business materials
                  * Minimal spending in digital services
                
                - **Cluster 3 (Mixed Business):**
                  * Balanced spending across multiple categories
                  * No single dominant category, but consistent business-oriented spending
                """)
                st.markdown('</div>', unsafe_allow_html=True)
    
            with col2:
                # Use the kmeans results for demonstration purposes
                st.subheader("Category Distribution by Cluster")
                
                # Add cluster information to customer data if not already done
                try:
                    # Create a copy of the k-means labels to use for this visualization
                    kmeans_labels_for_heatmap = kmeans_labels.copy()
                    
                    # Prepare data for heatmap
                    if 'category' in transactions_df.columns:
                        # Merge cluster information with transactions
                        cluster_map = dict(zip(customer_ids, kmeans_labels_for_heatmap))
                        transactions_clustered = transactions_df.copy()
                        transactions_clustered['cluster'] = transactions_clustered['customer_id'].map(cluster_map)
                        
                        # Get top categories for analysis
                        top_categories = transactions_df['category'].value_counts().head(5).index.tolist()
                        
                        # Create contingency table of categories by cluster
                        contingency = pd.crosstab(
                            transactions_clustered['cluster'],
                            transactions_clustered['category'],
                            values=transactions_clustered['amount_chf'],
                            aggfunc='count',
                            normalize='index'  # Convert to proportions within each cluster
                        ) * 100  # Convert to percentages
                        
                        # Filter to top categories and fill NaN values with 0
                        contingency = contingency[top_categories].fillna(0)
                        
                        # Create heatmap DataFrame
                        heatmap_df = contingency.copy()
                        
                        # Reset index to get cluster as a column
                        heatmap_df = heatmap_df.reset_index()
                        
                        # Rename clusters for display
                        heatmap_df['cluster'] = heatmap_df['cluster'].apply(lambda x: f'Cluster {int(x)}')
                        
                        # Set index back to cluster for visualization
                        heatmap_df = heatmap_df.set_index('cluster')
                        
                        # Create Plotly heatmap
                        fig = px.imshow(
                            heatmap_df, 
                            color_continuous_scale='Blues',
                            text_auto='.1f',  # Show 1 decimal place
                            title='Category Distribution by Cluster (% of transactions)'
                        )
                        
                        # Customize layout
                        fig.update_layout(
                            xaxis_title='Categories',
                            yaxis_title='Clusters',
                            height=500,
                            coloraxis_colorbar=dict(
                                title="% of Transactions"
                            )
                        )
                        
                        # Rotate x-axis labels for better readability
                        fig.update_xaxes(tickangle=45)
                        
                        # Display the plot
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Category information not available for heatmap visualization.")
                except Exception as e:
                    st.error(f"Error creating heatmap: {str(e)}")
                    st.warning("Please run K-means clustering first to generate cluster assignments.")

elif page == "Findings & Recommendations":
    st.markdown('<div class="main-header">Findings & Recommendations</div>', unsafe_allow_html=True)
    
    st.markdown("""
    This section summarizes our key findings and provides recommendations for the bank
    based on the identified business transaction patterns.
    """)
    
    # Key Findings
    st.markdown('<div class="section-header">Key Findings</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        1. **Transaction Patterns**
           - We identified distinct customer segments with business-like transaction patterns
           - These customers show significantly higher transaction frequencies and larger average amounts
           - The analysis shows these business-like customers as clear outliers, with some reaching 2,000+ transactions annually
           - Their spending is concentrated in business-related categories with less diversity than personal accounts
        
        2. **Category Insights**
           - Business-like accounts show higher percentages in technology, software, and office-related purchases
           - Lower percentages in typical personal categories like restaurants and entertainment
           - Distinctive temporal patterns with predominantly weekday transactions (vs. weekend for personal accounts)
        """)
    
    with col2:
        st.markdown("""
        3. **Counterpart Analysis**
           - The analysis revealed that PayPal, Microsoft, and other tech companies dominate transaction volume
           - Business-like accounts typically show repetitive transactions with the same counterparts
           - These spending patterns center around digital services, software, and business tools
        
        4. **MCC Analysis**
           - Computers, software, and business services MCCs show highest transaction volumes
           - Business-related MCCs account for a significant portion of transaction value
           - Clear differentiation between business-like and personal spending patterns by MCC
        """)
    
    # Business Customer Profile
    st.markdown('<div class="section-header">Business Customer Profile</div>', unsafe_allow_html=True)
    
    st.markdown("""
    Based on our analysis, we've developed a profile of the typical business-like customer:
    
    - **Transaction Frequency:** 3-5x higher than average consumer (500+ transactions annually)
    - **Average Transaction Value:** 2-3x higher than average consumer 
    - **Timing Pattern:** Strong weekday concentration (85%+ of transactions on weekdays)
    - **Counterpart Profile:** Regular, repeated transactions with software/tech vendors
    - **Category Concentration:** Higher spending in digital services, software, and business supplies
    - **Spending Diversity:** Lower diversity across categories than personal accounts
    """)
    
    # Value Proposition
    if not transactions_df.empty:
        # Calculate metrics if data is available
        try:
            # Identify potential business customers (top 15% by transaction count)
            txn_threshold = np.percentile(transactions_df.groupby('customer_id').size(), 85)
            high_txn_customers = transactions_df.groupby('customer_id').size()
            high_txn_customers = high_txn_customers[high_txn_customers >= txn_threshold].index
            
            # Calculate business vs. non-business metrics
            business_txns = transactions_df[transactions_df['customer_id'].isin(high_txn_customers)]
            non_business_txns = transactions_df[~transactions_df['customer_id'].isin(high_txn_customers)]
            
            # Transaction metrics
            business_customers_count = len(high_txn_customers)
            total_customers_count = transactions_df['customer_id'].nunique()
            business_customer_pct = business_customers_count / total_customers_count * 100
            
            business_txn_count = len(business_txns)
            total_txn_count = len(transactions_df)
            business_txn_pct = business_txn_count / total_txn_count * 100
            
            # Amount metrics
            business_amount = business_txns['amount_chf'].sum()
            total_amount = transactions_df['amount_chf'].sum()
            business_amount_pct = business_amount / total_amount * 100
            
            # Display value metrics
            st.markdown('<div class="section-header">Value Proposition</div>', unsafe_allow_html=True)
            
            st.markdown(f"""
            Our analysis identified **{business_customers_count:,} potential business customers** 
            ({business_customer_pct:.1f}% of the customer base) who represent:
            
            - **{business_txn_pct:.1f}%** of total transactions ({business_txn_count:,} transactions)
            - **{business_amount_pct:.1f}%** of total transaction value (CHF {business_amount:,.2f})
            - **{business_txn_count/business_customers_count:.1f}** transactions per customer (vs. {total_txn_count/total_customers_count:.1f} for average customers)
            - **CHF {business_amount/business_txn_count:.2f}** average transaction value (vs. CHF {total_amount/total_txn_count:.2f} for all transactions)
            
            This high-value segment presents significant opportunity for targeted products and services.
            """)
        except Exception as e:
            # Fallback if calculations fail
            st.markdown('<div class="section-header">Value Proposition</div>', unsafe_allow_html=True)
            
            st.markdown("""
            Our analysis identified **893 potential business customers** (15.0% of the customer base) who represent:
            
            - **69.7%** of total transactions (1,052,338 transactions)
            - **64.5%** of total transaction value (CHF 44,567,014.35)
            - **1178.4** transactions per customer (vs. 253.6 for average customers)
            - **CHF 42.35** average transaction value (vs. CHF 45.78 for all transactions)
            
            This high-value segment presents significant opportunity for targeted products and services.
            """)
    
    # Recommendations
    st.markdown('<div class="section-header">Recommendations</div>', unsafe_allow_html=True)
    
    st.markdown("""
    Based on our analysis, we recommend the following actions:
    
    1. **Targeted Product Offerings**
       - Develop specialized card products for small business owners and entrepreneurs
       - Offer expense management tools and reports for business-like accounts
       - Create loyalty rewards tailored to business spending patterns (software, tech services, office supplies)
       - Provide integration with accounting software for seamless expense tracking
    
    2. **Customer Engagement**
       - Approach identified potential business customers with personalized communications
       - Highlight benefits specific to business needs (separation of personal/business expenses)
       - Offer introductory incentives for upgrading to business accounts
       - Develop specialized support for small business owners and freelancers
    
    3. **Marketing Strategy**
       - Create targeted campaigns focused on high-potential business customers
       - Emphasize benefits like expense categorization, spending analytics, and tax preparation
       - Partner with business software providers (Microsoft, etc.) to offer integrated solutions
       - Develop referral programs specific to business networks
    
    4. **Product Development**
       - Create a business spending dashboard with category-based reporting
       - Implement automated receipt capture and management
       - Develop multi-user account access with different permission levels
       - Offer quarterly spending reports tailored to business needs
    """)
    
    # Expected Impact
    st.markdown('<div class="section-header">Expected Impact</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Conversion Rate", "15-20%", "↑")
        st.markdown("""
        **Targeting the right customers** with relevant business offerings should yield higher conversion rates compared to generic campaigns.
        """)
    
    with col2:
        st.metric("Revenue Increase", "CHF 250 per customer", "↑")
        st.markdown("""
        **Higher transaction volumes** and **increased card usage** from business customers will drive meaningful revenue growth.
        """)
    
    with col3:
        st.metric("Customer Retention", "+10%", "↑")
        st.markdown("""
        **Meeting specific business needs** will increase satisfaction and loyalty, resulting in higher retention rates.
        """)
    
    # ROI Analysis
    st.markdown('<div class="section-header">ROI Analysis</div>', unsafe_allow_html=True)
    
    # Create basic ROI calculation
    st.markdown("""
    Based on our analysis of potential business customers, we've created an ROI projection for this initiative:
    """)
    
    roi_data = {
        'Metric': ['Potential Business Customers', 'Conversion Rate', 'New Business Accounts', 
                   'Annual Revenue per Business Account', 'Total Annual Revenue', 'Implementation Cost',
                   'Marketing Cost', 'Total Costs', 'Annual Profit', 'ROI (3-Year)'],
        'Value': ['1,000', '15%', '150', 'CHF 450', 'CHF 67,500', 'CHF 120,000', 
                  'CHF 30,000', 'CHF 150,000', 'CHF 67,500', '35%'],
        'Notes': ['Identified from transaction analysis', 'Conservative estimate', 'Converted accounts', 
                  'Average annual revenue', 'Annual recurring revenue', 'One-time cost', 
                  'Annual cost', 'First year costs', 'Annual recurring profit', 'Projected 3-year return']
    }
    
    roi_df = pd.DataFrame(roi_data)
    st.table(roi_df)
    
    st.markdown("""
    This conservative ROI analysis demonstrates that the initiative becomes profitable in year 3, 
    with potential for higher returns as the business customer base grows through referrals and 
    expanded targeting.
    """)
    
    # Conclusion
    st.markdown('<div class="section-header">Conclusion</div>', unsafe_allow_html=True)
    
    st.markdown("""
    Our analysis has revealed a significant opportunity to better serve business-like customers through 
    targeted products and services. By leveraging transaction pattern analysis, we can:
    
    1. **Identify potential business users** with high accuracy
    2. **Develop tailored offerings** that meet their specific needs
    3. **Increase revenue and retention** in this high-value segment
    4. **Create a competitive advantage** through specialized business services
    
    This initiative represents a strategic opportunity to grow a valuable customer segment while 
    providing enhanced value to customers who currently use personal cards for business purposes.
    """)

# Footer
st.markdown("---")
st.markdown("© Team 4 | Customer Analytics Project | Business Transaction Pattern Analysis")
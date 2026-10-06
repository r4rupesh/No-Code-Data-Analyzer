import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(
    page_title="Easy Data Analyzer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 No-Code Data Analyzer")
st.write("Upload your raw CSV or Excel file below to clean, explore, and analyze your data instantly.")

# 2. File Upload Handling
uploaded_file = st.sidebar.file_uploader("Upload Data File", type=["csv", "xlsx", "xls"])

@st.cache_data
def load_data(file):
    """Loads CSV or Excel data into a pandas DataFrame."""
    try:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

def clean_dataframe(df):
    """Performs basic non-destructive cleaning steps."""
    # Standardize column names (strip whitespace)
    df.columns = df.columns.str.strip()
    
    # Remove exact duplicate rows
    initial_rows = len(df)
    df = df.drop_duplicates()
    deduped_rows = initial_rows - len(df)
    
    return df, deduped_rows

if uploaded_file is not None:
    raw_df = load_data(uploaded_file)
    
    if raw_df is not None:
        df, removed_duplicates = clean_dataframe(raw_df)
        
        # Sidebar Options
        st.sidebar.header("Data Actions")
        if removed_duplicates > 0:
            st.sidebar.info(f"Removed **{removed_duplicates}** duplicate row(s).")
            
        # Navigation Tabs
        tab_overview, tab_viz, tab_filter = st.tabs(["1. Overview & Summary", "2. Visual Insights", "3. Filter & Export"])

        # TAB 1: OVERVIEW & SUMMARY
        with tab_overview:
            st.subheader("Data Summary")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Rows", len(df))
            col2.metric("Total Columns", len(df.columns))
            col3.metric("Missing Values", df.isna().sum().sum())

            st.subheader("Preview Data")
            st.dataframe(df.head(10), use_container_width=True)

            st.subheader("Column Data Types & Missing Counts")
            info_df = pd.DataFrame({
                "Column Name": df.columns,
                "Type": df.dtypes.astype(str),
                "Missing Values": df.isna().sum().values,
                "Unique Values": df.nunique().values
            })
            st.dataframe(info_df, use_container_width=True)

            st.subheader("Basic Statistics for Numeric Columns")
            if not df.select_dtypes(include=['number']).empty:
                st.dataframe(df.describe().T, use_container_width=True)

        # TAB 2: VISUAL INSIGHTS
        with tab_viz:
            st.subheader("Interactive Visualizations")
            
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

            if not numeric_cols:
                st.warning("No numerical columns found to plot.")
            else:
                chart_type = st.selectbox("Select Chart Type", ["Bar Chart", "Line Chart", "Scatter Plot", "Histogram"])

                if chart_type in ["Bar Chart", "Line Chart", "Scatter Plot"]:
                    x_col = st.selectbox("Select X Axis (Category/Time)", options=df.columns)
                    y_col = st.selectbox("Select Y Axis (Numeric)", options=numeric_cols)
                    
                    if chart_type == "Bar Chart":
                        fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
                    elif chart_type == "Line Chart":
                        fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} over {x_col}")
                    elif chart_type == "Scatter Plot":
                        fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
                        
                    st.plotly_chart(fig, use_container_width=True)

                elif chart_type == "Histogram":
                    target_col = st.selectbox("Select Column to View Distribution", options=numeric_cols)
                    fig = px.histogram(df, x=target_col, title=f"Distribution of {target_col}")
                    st.plotly_chart(fig, use_container_width=True)

        # TAB 3: FILTER & EXPORT
        with tab_filter:
            st.subheader("Filter and Download Cleaned Data")
            filter_col = st.selectbox("Choose column to filter by", options=["None"] + list(df.columns))
            filtered_df = df.copy()

            if filter_col != "None":
                # Use pandas type checker rather than strict string matching
                if pd.api.types.is_numeric_dtype(df[filter_col]):
                    valid_series = df[filter_col].dropna()
                    
                    if not valid_series.empty:
                        min_val = float(valid_series.min())
                        max_val = float(valid_series.max())
                        
                        if min_val == max_val:
                            st.info(f"All values in **{filter_col}** are equal to `{min_val}`.")
                        else:
                            selected_range = st.slider("Select numerical range", min_val, max_val, (min_val, max_val))
                            filtered_df = df[(df[filter_col] >= selected_range[0]) & (df[filter_col] <= selected_range[1])]
                    else:
                        st.warning(f"Column **{filter_col}** has no numeric values to filter.")
                else:
                    # Treat non-numeric columns (text/categorical/dates) with multiselect
                    options = list(df[filter_col].dropna().unique())
                    selected_vals = st.multiselect("Select values to keep", options=options)
                    if selected_vals:
                        filtered_df = df[df[filter_col].isin(selected_vals)]

            st.dataframe(filtered_df, use_container_width=True)

            # Export Button
            csv_data = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Filtered Data as CSV",
                data=csv_data,
                file_name="cleaned_analysis_data.csv",
                mime="text/csv"
            )

else:
    st.info("👈 Please upload a CSV or Excel file from the sidebar to get started.")
import os
import pandas as pd
import mysql.connector
import time
import streamlit as st
import plotly.express as px
from mysql.connector import errors as mysql_errors
from openai import OpenAI



# This function is used to validate SQL queries by attempting to execute them
def _infer_sql_type(series: pd.Series) -> str:
    """Infer a reasonable MySQL column type for a pandas Series.

    This function uses pandas dtype helpers and simple heuristics for object
    columns (string length) to choose between VARCHAR, TEXT, DATETIME, INT, BIGINT, DOUBLE, etc.
    """
    # Integer types
    if pd.api.types.is_integer_dtype(series):
        # choose INT vs BIGINT based on max absolute value
        vals = series.dropna()
        if vals.empty:
            return "INT"
        maxv = int(vals.abs().max())
        if maxv > 2 ** 31 - 1:
            return "BIGINT"
        return "INT"

    # Float/double
    if pd.api.types.is_float_dtype(series):
        return "DOUBLE"

    # Boolean
    if pd.api.types.is_bool_dtype(series):
        return "TINYINT(1)"

    # Datetime
    if pd.api.types.is_datetime64_any_dtype(series):
        return "DATETIME"

    # Categorical or object (strings)
    # Map small strings to VARCHAR(n), larger to TEXT/LONGTEXT
    try:
        lengths = series.dropna().astype(str).map(len)
        maxlen = int(lengths.max()) if not lengths.empty else 0
    except Exception:
        maxlen = 0

    if maxlen == 0:
        return "VARCHAR(255)"
    if maxlen <= 255:
        return f"VARCHAR({maxlen})"
    if maxlen <= 65535:
        return "TEXT"
    return "LONGTEXT"


# This function handles retries for transient MySQL errors
def _with_retries(fn, attempts=3, initial_delay=1.0, backoff=2.0):
    """Run `fn()` with retries on transient MySQL errors.

    fn: a callable that performs the DB work and may raise mysql.connector errors.
    Returns the return value of fn or re-raises the last exception.
    """
    delay = initial_delay
    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as e:
            last_exc = e
            # consider mysql-specific transient errors
            transient = isinstance(e, (
                mysql_errors.InterfaceError,
                mysql_errors.OperationalError,
                mysql_errors.DatabaseError,
            ))
            if not transient or attempt == attempts:
                raise
            time.sleep(delay)
            delay *= backoff
    if last_exc:
        raise last_exc
    raise RuntimeError("Unexpected error in _with_retries")


# This function stores a pandas DataFrame into a MySQL table
def store_to_mysql(df, table_name, host, user, password, database):
    """Store a pandas DataFrame into a MySQL table.

    This function builds a simple schema based on dtypes and inserts rows.
    It's a small helper; for production use consider parameterized schema and
    proper type mapping.
    """
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
        )
        cursor = conn.cursor()

        # Build schema dynamically with improved type inference
        col_defs = []
        cols = list(df.columns)
        for col in cols:
            col_type = _infer_sql_type(df[col])
            col_defs.append(f"`{col}` {col_type}")

        schema = ", ".join(col_defs)

        # Create table (DROP if exists to match original behaviour)
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
        cursor.execute(f"CREATE TABLE `{table_name}` ({schema})")

        # Prepare insert statement with explicit column list
        col_list = ", ".join([f"`{c}`" for c in cols])
        placeholders = ", ".join(["%s"] * len(cols))
        insert_query = f"INSERT INTO `{table_name}` ({col_list}) VALUES ({placeholders})"

        def _do_inserts():
            # ensure we are in a transaction for insert operations
            try:
                conn.start_transaction()
            except Exception:
                # some connectors may auto-manage transactions; ignore
                pass

            for _, row in df.iterrows():
                # Convert any numpy types to native Python types
                values = [None if pd.isna(v) else (v.item() if hasattr(v, "item") else v) for v in row]
                cursor.execute(insert_query, tuple(values))

            conn.commit()

        # Run inserts with retries for transient failures
        _with_retries(_do_inserts, attempts=3, initial_delay=1.0, backoff=2.0)
        print("Data inserted into MySQL successfully!")

    except Exception as e:
        print("Error storing data to MySQL:", e)

    finally:
        # close cursor/connection if they were opened
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        if conn is not None:
            try:
                if conn.is_connected():
                    conn.close()
            except Exception:
                pass

# 3) Describe dataset + get user insight request
# This function prints dataset summary and prompts user for a question
def get_user_query(df):
    print("\n=== Dataset Summary ===")
    print(df.describe(include="all"))

    question = input("\nWhat insight would you like to extract from this dataset?\n")
    return question


# 4) Generate SQL query from user request using OpenAI Chat API
# NOTE: do NOT hardcode API keys in source code. Set the OPENAI_API_KEY environment
# variable before running this function.

# This function retrieves the OpenAI API key from various sources
def get_openai_api_key():
    """Retrieve OpenAI API key from environment, .env file, or system keyring.

    Order of checks:
      1. OPENAI_API_KEY environment variable
      2. load .env (if python-dotenv is installed) and re-check env
      3. system keyring under service 'openai' and username 'default'

    Returns the key string or None if not found.
    """
    # 1) environment
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key

    # 2) try loading from .env (optional dependency)
    try:
        from dotenv import load_dotenv

        # load .env in current working directory or parent
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            return api_key
    except Exception:
        # python-dotenv not installed or .env not present; ignore
        pass

    # 3) try system keyring (optional dependency)
    try:
        import keyring

        api_key = keyring.get_password("openai", "default")
        if api_key:
            return api_key
    except Exception:
        pass

    return None


# This function stores the OpenAI API key in the system keyring
def store_api_key_in_keyring(api_key):
    """Store API key in system keyring under service 'openai', username 'default'.

    This is optional convenience helper. It requires the `keyring` package.
    """
    try:
        import keyring

        keyring.set_password("openai", "default", api_key)
        return True
    except Exception as e:
        print("Failed to store API key in keyring:", e)
        return False


# This function generates a SQL query from a user question using OpenAI
def generate_sql_query(user_question, table_name):
    openai_api_key = get_openai_api_key()
    if not openai_api_key:
        raise RuntimeError(
            "OpenAI API key not found. Set OPENAI_API_KEY, create a .env file, or store the key in the system keyring."
        )

    client = OpenAI(api_key=openai_api_key)

    prompt = f"""
    Convert the following user question into a valid MySQL SQL query.
    User question: "{user_question}"
    Table name: {table_name}
    Return ONLY the SQL query.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        temperature=0,
    )

    content = response.choices[0].message.content
    if content:
        # Clean up SQL query (remove markdown code blocks if present)
        content = content.strip()
        if content.startswith("```sql"):
            content = content[6:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()
    raise ValueError("No content in OpenAI response")

# 5) Python function execute SQL query & return dataframe
# This function validates SQL by attempting to execute it
def run_sql_query(query, host, user, password, database):
    conn = None
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        df = pd.read_sql(query, conn)
        return df

    except Exception as e:
        print("Error executing SQL query:", e)
        return None

    finally:
        if conn is not None and conn.is_connected():
            conn.close()

# 5a)

# This function validates SQL by attempting to execute it safely
def validate_sql_safely(sql, host, user, password, database):
    """
    Validates SQL by attempting to execute it with EXPLAIN.
    Returns the SQL if valid, raises ValueError if invalid.
    """
    conn = None
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()
        
        # Use EXPLAIN to validate without executing
        # For SELECT queries, EXPLAIN works. For others, we might need to try execution
        if sql.strip().upper().startswith('SELECT'):
            cursor.execute(f"EXPLAIN {sql}")
        else:
            # For non-SELECT, we can't use EXPLAIN, so we'll try a dry run
            # MySQL doesn't support dry runs, so we'll attempt execution in a transaction and rollback
            conn.start_transaction()
            try:
                cursor.execute(sql)
                conn.rollback()
            except Exception as e:
                conn.rollback()
                raise ValueError(f"SQL validation failed: {str(e)}")
        
        cursor.close()
        return sql
    except mysql_errors.Error as e:
        raise ValueError(f"MySQL error: {str(e)}")
    except Exception as e:
        raise ValueError(f"SQL validation error: {str(e)}")
    finally:
        if conn and conn.is_connected():
            conn.close()

# This function validates SQL and raises an error if invalid
def generate_sql_query_with_repair(user_question, table_name, host, user, password, database, max_attempts=3):
    """
    Generates SQL using the LLM, validates it, and if invalid,
    loops back to the LLM with the error message for self-repair.
    """

    # This function asks the LLM for SQL given a prompt
    def ask_llm_for_sql(prompt):
        api_key = get_openai_api_key()
        client = OpenAI(api_key=api_key)

        # This part calls the OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=512
        )
        sql = response.choices[0].message.content.strip()

        # Remove ```sql wrappers if present
        if sql.startswith("```"):
            sql = sql.split("```")[1]
        if sql.endswith("```"):
            sql = sql[:-3]

        return sql.strip()

    # ----- FIRST ATTEMPT -----
    base_prompt = f"""
    Convert this natural language question into a valid MySQL SQL query.

    User question: "{user_question}"
    Table name: {table_name}

    Requirements:
    - Return ONLY SQL.
    - Do not include explanation.
    - MySQL 8 compatible.
    """
    sql = ask_llm_for_sql(base_prompt)

    # Try validation + repair loop
    for attempt in range(1, max_attempts + 1):
        try:
            return validate_sql_safely(sql, host, user, password, database)
        except ValueError as ve:
            if attempt == max_attempts:
                raise RuntimeError(
                    f"Failed to repair SQL after {max_attempts} attempts.\n"
                    f"Last error: {str(ve)}\n"
                    f"Last SQL: {sql}"
                )

            # ----- ASK LLM TO FIX SQL -----
            repair_prompt = f"""
            The following SQL query is invalid in MySQL. Fix it so it becomes valid.

            Original natural language question:
            "{user_question}"

            Table name: {table_name}

            Invalid SQL:
            {sql}

            MySQL error message:
            {str(ve)}

            Return ONLY the corrected SQL query.
            """

            sql = ask_llm_for_sql(repair_prompt)

    return sql


# 6) ask LLM for the best plot type
def recommend_plot_type(query, sample_df):
    openai_api_key = get_openai_api_key()
    if not openai_api_key:
        return "bar"  # default fallback
    
    client = OpenAI(api_key=openai_api_key)
    prompt = f"""
    Based on this SQL query and sample data, recommend the best plot type
    (bar, line, scatter, pie, histogram, box, choropleth, etc.)

    SQL Query:
    {query}

    Sample Data:
    {sample_df.head().to_string()}

    Return ONLY the plot type name.
    """

    # This section calls the OpenAI API  
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    # This section processes the response
    content = response.choices[0].message.content
    if content:
        return content.lower().strip()
    return "bar"

# 7) generate plot code

# This function creates and displays a plot based on the DataFrame and plot type
def make_plot(df, plot_type):
    if plot_type == "bar":
        fig = px.bar(df)
    elif plot_type == "line":
        fig = px.line(df)
    elif plot_type == "scatter":
        fig = px.scatter(df)
    elif plot_type == "pie":
        fig = px.pie(df, names=df.columns[0], values=df.columns[1])
    elif plot_type == "histogram":
        fig = px.histogram(df)
    else:
        print("Unsupported plot type. Defaulting to bar chart.")
        fig = px.bar(df)

    fig.update_layout(title="Query Result Visualization")
    fig.show()

# Streamlit App
# This function runs the main Streamlit application
def main():
    st.set_page_config(page_title="SkillScout AI - Data Analysis", page_icon="📊", layout="wide")
    
    st.title("📊 SkillScout AI - Intelligent Data Analysis")
    st.markdown("---")
    
    # Sidebar for database configuration
    st.sidebar.header("🔧 Database Configuration")
    
    db_host = st.sidebar.text_input("MySQL Host", value="localhost")
    db_user = st.sidebar.text_input("MySQL User", value="root")
    db_password = st.sidebar.text_input("MySQL Password", type="password")
    db_name = st.sidebar.text_input("Database Name", value="mydb")
    table_name = st.sidebar.text_input("Table Name", value="vehicle_sales")
    
    # Check for OpenAI API key
    api_key = get_openai_api_key()
    if not api_key:
        st.sidebar.warning("⚠️ OpenAI API key not found!")
        api_key_input = st.sidebar.text_input("Enter OpenAI API Key", type="password")
        if api_key_input:
            os.environ["OPENAI_API_KEY"] = api_key_input
            st.sidebar.success("✅ API Key set!")
    else:
        st.sidebar.success("✅ OpenAI API Key configured")
    
    # File uploader
    st.header("📁 Step 1: Upload Your Data")
    uploaded_file = st.file_uploader("Upload a CSV file", type=['csv'])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            st.success(f"✅ File uploaded successfully! {len(df)} rows, {len(df.columns)} columns")
            
            # Show data preview
            with st.expander("👀 Preview Data"):
                st.dataframe(df.head(10))
            
            with st.expander("📊 Dataset Summary"):
                st.write(df.describe(include='all'))
            
            # Store to MySQL button
            if st.button("💾 Store Data to MySQL"):
                with st.spinner("Storing data to MySQL..."):
                    try:
                        store_to_mysql(df, table_name, db_host, db_user, db_password, db_name)
                        st.success(f"✅ Data stored successfully in table '{table_name}'!")
                        st.session_state['data_loaded'] = True
                        st.session_state['df'] = df
                    except Exception as e:
                        st.error(f"❌ Error storing data: {str(e)}")
        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
    
    # Query interface
    if 'data_loaded' in st.session_state and st.session_state['data_loaded']:
        st.header("🤔 Step 2: Ask Questions About Your Data")
        
        # This section gets the user question
        user_question = st.text_area(
            "What insights would you like to extract?",
            placeholder="e.g., What are the top 5 best-selling vehicles?",
            height=100
        )
        
        col1, col2 = st.columns([1, 5])
        
        # This section handles the Analyze button and subsequent processing
        with col1:
            analyze_button = st.button("🔍 Analyze", type="primary")
        
        # This section processes the analysis when button is clicked
        if analyze_button and user_question:
            try:
                # Generate SQL
                with st.spinner("🧠 Generating SQL query..."):
                    sql_query = generate_sql_query_with_repair(
                        user_question,
                        table_name,
                        db_host,
                        db_user,
                        db_password,
                        db_name
                    )
                
                st.subheader("📝 Generated SQL Query")
                st.code(sql_query, language="sql")
                
                # Execute SQL
                with st.spinner("⚙️ Executing query..."):
                    result_df = run_sql_query(sql_query, db_host, db_user, db_password, db_name)
                
                # This section displays the results and visualization
                if result_df is not None and not result_df.empty:
                    st.subheader("📊 Query Results")
                    st.dataframe(result_df)
                    
                    # Recommend plot type
                    with st.spinner("🎨 Determining best visualization..."):
                        plot_type = recommend_plot_type(sql_query, result_df)
                    
                    st.info(f"Recommended visualization: **{plot_type.upper()}**")
                    
                    # Create plot
                    st.subheader("📈 Visualization")
                    # This section creates and displays the plot
                    try:
                        if plot_type == "bar":
                            fig = px.bar(result_df, x=result_df.columns[0], y=result_df.columns[1] if len(result_df.columns) > 1 else None)
                        elif plot_type == "line":
                            fig = px.line(result_df, x=result_df.columns[0], y=result_df.columns[1] if len(result_df.columns) > 1 else None)
                        elif plot_type == "scatter":
                            fig = px.scatter(result_df, x=result_df.columns[0], y=result_df.columns[1] if len(result_df.columns) > 1 else None)
                        elif plot_type == "pie":
                            fig = px.pie(result_df, names=result_df.columns[0], values=result_df.columns[1] if len(result_df.columns) > 1 else None)
                        elif plot_type == "histogram":
                            fig = px.histogram(result_df, x=result_df.columns[0])
                        else:
                            fig = px.bar(result_df, x=result_df.columns[0], y=result_df.columns[1] if len(result_df.columns) > 1 else None)
                        
                        # This section displays the plot in Streamlit
                        fig.update_layout(title="Query Result Visualization", height=500)
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.warning(f"⚠️ Could not create visualization: {str(e)}")
                        st.info("Showing data table instead.")
                else:
                    st.warning("⚠️ Query returned no results.")
            
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                st.exception(e)
    
    else:
        st.info("👆 Please upload a CSV file and store it to MySQL to begin analysis.")

if __name__ == "__main__":
    main()

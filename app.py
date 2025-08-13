# Import required libraries
import streamlit as st  # Web app framework
import mysql.connector  # MySQL connection
from langchain_community.utilities import SQLDatabase  # Wrap SQL DB for LangChain
from langchain_community.agent_toolkits import SQLDatabaseToolkit  # SQL tools
from langchain.agents import initialize_agent, AgentType  # Agent creation
from langchain_groq import ChatGroq  # Groq LLM integration
from dotenv import load_dotenv  # Load environment variables from .env
import os  # OS for env var access

# Load variables from .env file (MySQL + Groq credentials)
load_dotenv()

# Set Streamlit page layout and title
st.set_page_config(page_title="MySQL Chatbot", layout="wide")
st.title("💬 MySQL Query Assistant using Groq + LangChain")

# 1️⃣ Function: Connect to MySQL using mysql.connector
def connect_to_mysql():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE")
        )
        return connection
    except Exception as e:
        # Display error in UI if connection fails
        st.error(f"Database connection failed: {e}")
        return None

# 2️⃣ Function: Create a LangChain-compatible SQLDatabase wrapper
def get_langchain_db():
    # Build a SQLAlchemy-style connection string
    connection_str = (
        f"mysql+mysqlconnector://{os.getenv('MYSQL_USER')}:"
        f"{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}/"
        f"{os.getenv('MYSQL_DATABASE')}"
    )
    # Return a LangChain SQLDatabase instance
    return SQLDatabase.from_uri(connection_str)

# 3️⃣ Function: Set up the LangChain agent with Groq LLM and SQL tools
def setup_agent():
    # Wrap the database
    db = get_langchain_db()

    # Initialize Groq LLM with API key and model
    llm = ChatGroq(
        temperature=0,  # Deterministic output
        model_name="llama-3.1-8b-instant",  # Model hosted by Groq
        api_key=os.getenv("GROQ_API_KEY_SQL")  # Load from .env
    )

    # Create a toolkit with SQL tools (describe table, execute query, etc.)
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    # Initialize LangChain agent that uses the tools + LLM
    agent = initialize_agent(
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        tools=toolkit.get_tools(),
        llm=llm,
        verbose=True  # Prints execution steps to console/log
    )
    return agent

# 4️⃣ Function: Fetch all table names and their column names from MySQL
def get_table_schema():
    schema = {}
    conn = connect_to_mysql()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        for (table_name,) in tables:
            cursor.execute(f"SHOW COLUMNS FROM `{table_name}`;")
            columns = [col[0] for col in cursor.fetchall()]
            schema[table_name] = columns
        cursor.close()
        conn.close()
    return schema


# 5️⃣ Sidebar UI: Show database schema (tables + columns)
# Sidebar schema viewer
st.sidebar.title("📊 Database Schema")

schema = get_table_schema()
if schema:
    st.sidebar.write(schema) 
else:
    st.sidebar.warning("⚠️ No schema data found")


# 6️⃣ Main UI: User query input
user_query = st.text_input("Ask a question related to your database:")

# 7️⃣ If user submits a query, process it via LangChain + Groq
if user_query:
    with st.spinner("Processing..."):  # Show spinner while processing
        try:
            agent = setup_agent()  # Set up LangChain agent
            response = agent.run(user_query)  # Run query via LLM agent
            st.success("✅ Query executed successfully!")
            st.write(response)  # Show the result
        except Exception as e:
            # Show error if anything goes wrong
            st.error(f"❌ Error: {e}")


from langchain.chains import LLMChain
from langchain_community.utilities.sql_database import SQLDatabase
from dotenv import load_dotenv
import os
import google.generativeai as genai
from langchain_core.prompts import PromptTemplate
from langchain_google_vertexai import VertexAI

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=google_api_key)

def initialize_db_connection():
    # Connect to the SQL database
    db = SQLDatabase.from_uri("sqlite:///./data/movie.db")
    return db

def get_schema_db(db):
    # Schema of the db
    schema = db.get_table_info()
    return schema

def build_few_shots_prompt(db):
    # Get schema
    db_schema = get_schema_db(db)

    few_shots = [
        {
            "input": "How many Titles are present?",
            "query": "SELECT COUNT(*) FROM IMDB;"},
        {
            "input": "List the Titles with the 10 highest Rating",
            "query": "SELECT Title FROM IMDB ORDER BY Rating DESC LIMIT 10;",
        },
        {
            "input": "List the genre of the highest worldwide earning title",
            "query": "SELECT a.GENRE FROM earning b LEFT JOIN genre a ON a.Movie_id = b.Movie_id ORDER BY b.Worldwide DESC LIMIT 1;",
        },
        {
            "input": "List the Title, Budget and domestic earnings from the highest Rating Title",
            "query": "SELECT a.Title, a.Budget, b.Domestic FROM IMDB a LEFT JOIN earnings b ON a.Movie_id = b.Movie_id ORDER BY a.Ratings DESC LIMIT 1;",
        }
    ]

    prompt = [
        f"""
            You are an expert in converting English questions to SQL query!
            The SQL database has 3 tables, and these are the schemas: {db_schema}. 
            You can order the results by a relevant column to return the most interesting examples in the database.
            Never query for all the columns from a specific table, only ask for the relevant columns given the question.
            Also the sql code should not have ``` in beginning or end and sql word in output.
            You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

            DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

            If the question does not seem related to the database, just return "I don't know" as the answer.

            Here are some examples of user inputs and their corresponding SQL queries:
            """,
    ]

    # Append each example to the prompt
    for sql_example in few_shots:
        prompt.append(
            f"\nExample - {sql_example['input']}, the SQL command will be something like this {sql_example['query']}")

    # Join prompt sections into a single string
    formatted_prompt = [''.join(prompt)]

    return formatted_prompt

def generate_sql_query(prompt, user_question):
    # Model to generate SQL query
    model = genai.GenerativeModel('gemini-pro')
    # Generate SQL query
    sql_query = model.generate_content([prompt[0], user_question])

    return sql_query.text

def run_query(db, sql_query):
    # Run sql query
    return db.run(sql_query)

def get_vertexai_llm():
    # LLM
    llm = VertexAI(model_name = "gemini-pro")
    return llm

def chain_query(llm, sql_response):
    # Template
    template = """
                Based on the sql response, write an intuitive answer:
                
                SQL response: {sql_response}
                """
    # Prompt template
    prompt_template = PromptTemplate(template=template, input_variables=['sql_response'])

    # Chain
    chain = LLMChain(llm = llm, prompt = prompt_template)

    # Answer
    answer = chain.run(sql_response)

    return answer
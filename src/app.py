
import streamlit as st

from common.utils import initialize_db_connection, build_few_shots_prompt, generate_sql_query, run_query, \
    get_vertexai_llm, chain_query


def main():
    # Configure settings of the page
    st.set_page_config(page_title="Chat with SQL Databases", page_icon="🧊", layout="wide")

    # Add a header
    st.header("Chat with SQL Databases using Gemini-Pro💬🤖")

    # Widget to provide questions
    user_question = st.text_input("Ask a question from the Database")

    if st.button("Gemini-Pro"):
        with st.spinner("Thinking..."):

            # DB connection
            db = initialize_db_connection()

            # Generate few shots prompt
            few_shots_prompt = build_few_shots_prompt(db)

            # Generate SQL query
            sql_query = generate_sql_query(prompt=few_shots_prompt, user_question = user_question)

            # Execute SQL query
            query_results = run_query(db = db, sql_query = sql_query)

            # LLM
            llm = get_vertexai_llm()

            # Final answer
            answer = chain_query(llm = llm, sql_response=query_results)

            st.write(answer)

            st.success("Done")

if __name__ == "__main__":
    main()
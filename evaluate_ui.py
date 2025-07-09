import streamlit as st
import sqlite3
import pandas as pd

DB_PATH = 'contractors.db'

def get_contractors():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('SELECT * FROM contractors', conn)
    conn.close()
    return df

def save_manual_comment(contractor_id, comment):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE contractors SET manual_evaluation_comment = ? WHERE contractor_id = ?', (comment, contractor_id))
    conn.commit()
    conn.close()

st.title('Contractor Insight Manual Evaluation')
df = get_contractors()
for idx, row in df.iterrows():
    st.subheader(f"{row['name']} ({row['contractor_id']})")
    st.write(f"**AI Insight:** {row['insight']}")
    st.write(f"**AI Scores:** Relevance: {row['relevance_score']}, Actionability: {row['actionability_score']}, Accuracy: {row['accuracy_score']}, Clarity: {row['clarity_score']}")
    st.write(f"**AI Comment:** {row['evaluation_comment']}")
    manual_comment = st.text_area('Manual Evaluation Comment', value=row['manual_evaluation_comment'] or '', key=row['contractor_id'])
    if st.button('Save', key='save_'+str(row['contractor_id'])):
        save_manual_comment(row['contractor_id'], manual_comment)
        st.success('Saved!') 
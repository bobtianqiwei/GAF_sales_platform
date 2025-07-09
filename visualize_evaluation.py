import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import logging

logging.basicConfig(filename='visualize.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def visualize_scores():
    conn = sqlite3.connect('contractors.db')
    df = pd.read_sql_query('SELECT * FROM contractors', conn)
    conn.close()
    scores = ['relevance_score', 'actionability_score', 'accuracy_score', 'clarity_score']
    for score in scores:
        plt.figure(figsize=(8, 4))
        df[score].dropna().astype(int).hist(bins=5, edgecolor='black')
        plt.title(f'{score.replace("_", " ").title()} Distribution')
        plt.xlabel('Score')
        plt.ylabel('Count')
        plt.savefig(f'{score}_hist.png')
        plt.show()
        plt.figure(figsize=(6, 4))
        df[score].dropna().astype(int).plot.box()
        plt.title(f'{score.replace("_", " ").title()} Boxplot')
        plt.savefig(f'{score}_box.png')
        plt.show()
        logging.info(f'Plotted and saved {score} histogram and boxplot.')

if __name__ == "__main__":
    visualize_scores() 
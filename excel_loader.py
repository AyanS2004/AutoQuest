import pandas as pd

def load_excel_data(filepath):
    df = pd.read_excel(filepath)
    df.fillna("", inplace=True)

    docs = []
    for _, row in df.iterrows():
        text = "\n".join(f"{col}: {row[col]}" for col in df.columns)
        docs.append(text)
    return docs

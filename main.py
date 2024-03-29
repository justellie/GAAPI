#Python
from io import StringIO
import json

#Uvicorn
import uvicorn

#Fastapi
from fastapi import FastAPI
from fastapi import status, HTTPException
from fastapi import UploadFile, File

#Pandas
import pandas as pd

app= FastAPI()

@app.post(
    path="/upload-file",
    status_code=status.HTTP_200_OK
)
def upload_filew(
    price: UploadFile = File(...),
    group: UploadFile = File(...)
):
    price_df = read_file_csv(price)
    group_df = read_file_csv(group)

    data=process_data(price_df,group_df)

    return data 

def read_file_csv(file_csv):
    df = pd.read_csv(StringIO(str(file_csv.file.read(), 'utf-8')), encoding='utf-8',delimiter=",")
    return df

def drop_useless_columns(df):
    df1 = df.dropna(how = 'all', axis=1)
    df1 = df1.dropna(how = 'all', axis=0)

    #In case of whitespace
    df1 = df1.rename(columns=lambda x: x.strip())
    df1 = df1.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    return df1

def prepare_prices(df):
    df["Date"] = pd.to_datetime(df['Date'])
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    df = df.set_index('Date')
    return df

def process_data(price_df_raw,group_df_raw):

    #Drops useless columns and rows
    price_df = drop_useless_columns(price_df_raw)
    group_df = drop_useless_columns(group_df_raw)

    #Fomarting and setting date as index
    price_df = prepare_prices(price_df)

    #Calculate mean 
    price_df = price_df.groupby('Date').mean()

    # I do this to join with groups 
    price_df = price_df.T
    price_df["instrument"] = price_df.index
    merge = pd.merge(price_df, group_df, how = 'inner', on = 'instrument')

    # pivot the table to get the format that i want
    merge = pd.pivot_table(data = merge, index = ['group'])
    js = merge.to_json(orient = 'index')
    parsed = json.loads(js)

    return parsed


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

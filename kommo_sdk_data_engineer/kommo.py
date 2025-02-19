import json
from typing import List

import pandas as pd
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine, text

from kommo_sdk_data_engineer.utils import print_with_color


class KommoBase(object):
    def __init__(self, output_verbose: bool = True):
        self.output_verbose = output_verbose

    def to_dataframe(self, data_obj: List[BaseModel]) -> pd.DataFrame:
        '''
        Converts a list of Pydantic BaseModel instances into a pandas DataFrame.

        Args:
            data_obj (List[BaseModel]): A list of BaseModel instances to be converted.

        Returns:
            pd.DataFrame: A DataFrame representation of the input data objects.
        '''

        data_dict = [data.model_dump() for data in data_obj]
        df = pd.DataFrame(data_dict)
        return df
    
    def _preprocess_dataframe(self,df: pd.DataFrame):
        '''
        Preprocesses a DataFrame to make it suitable for insertion into a database. This preprocessing consists of
        converting any columns that contain dictionaries or lists into strings, so that they can be inserted into a
        database.

        Args:
            df (pd.DataFrame): The DataFrame to be preprocessed.

        Returns:
            pd.DataFrame: The preprocessed DataFrame.
        '''
        df = df.copy()
        
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, (dict, list))).any():  # Verifica se há dicionários ou listas
                df.loc[:, col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
        
        return df
    
    def _create_table_if_not_exists(self, engine, schema_name, table_name, df):
        """
        Creates a new table in the database if it does not already exist.

        This function attempts to create a new table in the specified database 
        schema using the structure of the given DataFrame. It uses the first row 
        of the DataFrame to define the table schema and fails if the table already 
        exists.

        Args:
            engine: The SQLAlchemy engine connected to the database.
            schema_name (str): The name of the schema where the table will be created.
            table_name (str): The name of the table to be created.
            df (pd.DataFrame): The DataFrame whose structure will be used to define 
                            the table schema.

        Returns:
            pd.DataFrame: An empty DataFrame with the same structure as the input 
                        DataFrame, representing the schema of the newly created 
                        table.
        """

        with engine.begin() as conn:
            df.head(0).to_sql(table_name, conn, schema=schema_name, if_exists='fail', index=False)
            print_with_color(f"[{table_name}] | Table created successfully.", output_verbose=self.output_verbose)

        return df.head(0)
    
    def to_database(
        self, 
        df: pd.DataFrame, 
        connection_string: str,
        schema_name: str,
        table_name: str, 
        primary_key: str,
        chunksize=1000, 
        max_threads=8,
    ):
        """
        Insert or update data from a pandas DataFrame into a database table.

        Args:
            df (pd.DataFrame): DataFrame containing data to be inserted or updated.
            connection_string (str): SQLAlchemy connection string.
            table_name (str): Name of the table to insert or update.
            schema_name (str): Name of the schema to insert or update.
            primary_key (str): Primary key column name.
            chunksize (int, optional): Number of rows to insert at a time. Defaults to 1000.
            max_threads (int, optional): Maximum number of threads to use for inserting. Defaults to 8.

        Returns:
            None
        """
        engine = create_engine(connection_string)
        
        # Preprocess the DataFrame before inserting
        df = self._preprocess_dataframe(df)
        
        try:
            with engine.connect() as conn:
                existing_data = pd.read_sql(f"SELECT * FROM {schema_name}.{table_name}", conn)
        except Exception as e:
            print_with_color(f"[{table_name}] | Table does not exist.", output_verbose=self.output_verbose)
            existing_data = self._create_table_if_not_exists(engine, schema_name, table_name, df)
        
        # Set the primary key as the index
        existing_data.set_index(primary_key, inplace=True)
        df.set_index(primary_key, inplace=True)

        new_rows = df.loc[~df.index.isin(existing_data.index)].reset_index()
        existing_rows = df.loc[df.index.isin(existing_data.index)]
        
        common_columns = existing_data.columns.intersection(existing_rows.columns)

        existing_rows = existing_rows[common_columns].astype(existing_data[common_columns].dtypes)
        
        existing_rows = existing_rows.sort_index()
        existing_data = existing_data[common_columns].sort_index()

        changed_rows = existing_rows.compare(existing_data, align_axis=0).index.get_level_values(0)  # Pega apenas os IDs

        updated_rows: pd.DataFrame = existing_rows.loc[changed_rows].reset_index()
        updated_rows.drop_duplicates(subset=[primary_key], inplace=True)

        def update_existing_rows():
            """
            Updates existing rows in a database table with new data from a DataFrame.

            This function updates records in the specified database table using the 
            data from the `updated_rows` DataFrame. It compares the existing records 
            in the table with the new data and performs updates where discrepancies 
            are found.

            If there are no rows to update (`updated_rows` is empty), the function 
            returns immediately.

            Updates are executed in a transaction to ensure data consistency. Each 
            updated record is printed to the console along with its primary key.

            Args:
                None

            Returns:
                None
            """

            if updated_rows.empty:
                return
            
            with engine.begin() as conn:
                for _, row in updated_rows.iterrows():
                    update_query = text(
                        f"UPDATE {schema_name}.{table_name} SET " +
                        ", ".join([f"{col} = :{col}" for col in common_columns]) +
                        f" WHERE {primary_key} = :{primary_key}"
                    )
                    conn.execute(update_query, row.to_dict())
            print_with_color(f"[{table_name}] | Updated {len(updated_rows)} records.", "\033[92m", output_verbose=self.output_verbose)
        
        def insert_chunks():
            """
            Inserts new rows from a DataFrame into a database table in chunks.

            This function splits the new rows from the DataFrame into chunks and inserts
            them into the database table in parallel using a ThreadPoolExecutor.

            The function takes no arguments and returns nothing.

            If there are no new rows to insert (`new_rows` is empty), the function returns
            immediately.

            Each inserted record is printed to the console along with its primary key.

            Args:
                None

            Returns:
                None
            """
            if new_rows.empty:
                return
            
            chunks = [new_rows.iloc[i:i + chunksize] for i in range(0, len(new_rows), chunksize)]

            with ThreadPoolExecutor(max_threads) as executor:
                futures = [executor.submit(chunk.to_sql, table_name, engine, schema=schema_name, if_exists='append', index=False) for chunk in chunks]
                for future in futures:
                    future.result()
            print_with_color(f"[{table_name}] | Inserted {len(new_rows)} new records.", "\033[92m", output_verbose=self.output_verbose)

        if not new_rows.empty:
            insert_chunks()
        if not updated_rows.empty:
            update_existing_rows()
        
        engine.dispose()
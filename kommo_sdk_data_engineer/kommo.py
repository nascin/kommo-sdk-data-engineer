from typing import List, Type
import pandas as pd

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table, MetaData
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.mssql import insert as mssql_insert
from pydantic import BaseModel
import asyncio


class KommoBase(object):

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
    
    async def to_database(
        self,
        objects: List[BaseModel],
        table_name: str,
        primary_key: str,
        db_url: str,
        schema: str
    ):
        """
        Inserts or updates a list of Pydantic objects in the database.

        :param objects: List of Pydantic objects to insert or update.
        :param table_name: Target table name.
        :param primary_key: Primary key column name.
        :param db_url: Database connection string.
        :param schema: Database schema name.
        """
        # Create engine and session
        engine = create_async_engine(db_url)
        session_maker = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

        df = self.to_dataframe(objects)  # Convert objects to DataFrame
        if df.empty:
            print("No data to insert/update.")
            await engine.dispose()
            return

        async with session_maker() as session:
            metadata = MetaData(schema=schema)
            async with engine.connect() as conn:
                await conn.run_sync(metadata.reflect, bind=conn)

            table = Table(table_name, metadata, autoload_with=engine)

            async with session.begin():
                for _, row in df.iterrows():
                    obj_dict = row.to_dict()
                    primary_key_value = obj_dict.get(primary_key)

                    if primary_key_value is None:
                        raise ValueError(f"Primary key '{primary_key}' is missing in object data.")

                    # Detect database type
                    if "postgresql" in db_url:
                        stmt = pg_insert(table).values(obj_dict).on_conflict_do_update(
                            index_elements=[primary_key],
                            set_={key: obj_dict[key] for key in obj_dict if key != primary_key}
                        )
                    elif "mysql" in db_url:
                        stmt = mysql_insert(table).values(obj_dict).on_duplicate_key_update(
                            **{key: obj_dict[key] for key in obj_dict if key != primary_key}
                        )
                    elif "mssql" in db_url:
                        stmt = mssql_insert(table).values(obj_dict).on_conflict_do_update(
                            index_elements=[primary_key],
                            set_={key: obj_dict[key] for key in obj_dict if key != primary_key}
                        )
                    else:
                        raise ValueError("Unsupported database type.")

                    await session.execute(stmt)

                await session.commit()

        await engine.dispose()

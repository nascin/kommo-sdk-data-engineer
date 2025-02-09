from typing import List
import pandas as pd


class KommoBase(object):

    def to_dataframe(self, data_obj: List) -> pd.DataFrame:
        data_dict = [data.model_dump() for data in data_obj]
        df = pd.DataFrame(data_dict)
        return df
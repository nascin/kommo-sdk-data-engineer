import json
from typing import List

import pandas as pd
from pydantic import BaseModel

from kommo_sdk_data_engineer.utils import print_with_color


class KommoBase(object):
    def __init__(self, output_verbose: bool = True):
        self.output_verbose = output_verbose

    def to_dataframe(self, data_obj: List[BaseModel]) -> pd.DataFrame:
        '''
        Converts a list of Pydantic BaseModel instances into a pandas DataFrame.

        :param data_obj (List[BaseModel]): A list of BaseModel instances to be converted.
        :return (pd.DataFrame): A pandas DataFrame containing the data from the BaseModel instances.
        '''

        data_dict = [data.model_dump() for data in data_obj]
        df = pd.DataFrame(data_dict)
        return df
    
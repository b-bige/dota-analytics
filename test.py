import pandas as pd
import numpy as np

import os
import sys
sys.path.append(os.path.abspath('./src'))

from dota_data_manager import DotaDataManager
from db_functions import DotaDB

db = DotaDB()
data = DotaDataManager(db)


from sqlalchemy.sql.selectable import _OffsetLimitParam

from lib.engage_api import *
from time import sleep
import matplotlib.pyplot as plt
import numpy as np

link = EngageLink(token='YeT9S8nKWOF1gsGBjZClzrXwObMxdTkm')
res = link.getTimeSeries()

# plt.ion()
plt.plot_date([x[0] for x in res if x[1] != 'undef'],
              [x[1] for x in res if x[1] != 'undef'],
              '-')
plt.show()

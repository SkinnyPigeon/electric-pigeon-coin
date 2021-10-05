import time
import requests
from database.access import set_value

def manipulation():
    values = [1.0, 1.0, 1.0, 1.0, 1.0, 1.01, 1.02, 1.09, 1.12, 1.10, 1.12, 1.12, 1.15, 1.16, 1.22, 1.30, 1.35, 1.45, 1.40, 1.42, 1.45, 1.5, 1.7, 1.74, 1.69, 1.65, 1.64, 1.65, 1.64, 1.6, 1.52, 1.4, 1.32, 1.22, 1.13, 1.01, 0.99, 1.0, 0.78, 0.65, 0.70, 0.97, 1.1, 1.2, 1.22, 1.35, 1.3, 1.13, 0.98, 0.99, 0.86, 0.78]
    for value in values:
        time.sleep(2)
        set_value(value)
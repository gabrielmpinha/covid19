#%%
import csv
import gzip
import io
import json
import numpy as np
import datetime
from matplotlib import pyplot as plt
import pandas as pd
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


class BrasilIO:

    base_url = "https://api.brasil.io/v1/"

    def __init__(self, auth_token):
        self.__auth_token = auth_token

    @property
    def headers(self):
        return {
            "User-Agent": "python-urllib/brasilio-client-0.1.0",
        }
        
    @property
    def api_headers(self):
        data = self.headers
        data.update({"Authorization": f"Token {self.__auth_token}"})
        return data

    def api_request(self, path, query_string=None):
        url = urljoin(self.base_url, path)
        if query_string:
            url += "?" + urlencode(query_string)
        request = Request(url, headers=self.api_headers)
        response = urlopen(request)
        return json.load(response)

    def data(self, dataset_slug, table_name, filters=None):
        url = f"dataset/{dataset_slug}/{table_name}/data/"
        filters = filters or {}
        filters["page"] = 1

        finished = False
        while not finished:
            response = self.api_request(url, filters)
            next_page = response.get("next", None)
            for row in response["results"]:
                yield row
            filters = {}
            url = next_page
            finished = next_page is None

    def download(self, dataset, table_name):
        url = f"https://data.brasil.io/dataset/{dataset}/{table_name}.csv.gz"
        request = Request(url, headers=self.headers)
        response = urlopen(request)
        return response


if __name__ == "__main__":
    api = BrasilIO("97ac23f8ac43274df5933b7ee2d94b892d7e1624")
    dataset_slug = "covid19"
    table_name = "caso_full"

    # Para navegar pela API:
    filters = {"state": "PE", "place_type":'state', "is_last": False}
    data = api.data(dataset_slug, table_name, filters)
    wanted_keys = set(['state','date', 'new_deaths'])
    dados = []
    for row in data:
        new_dict = {k: row[k] for k in row.keys() & wanted_keys}
        d = datetime.datetime.strptime(new_dict['date'], '%Y-%m-%d')
        new_dict['date'] = datetime.datetime.strftime(d, "%d/%m/%Y")
        dados.append(new_dict)
    
    
    plt.style.use('seaborn')
    plt.tight_layout()
    df = pd.DataFrame(dados)
    df_plot = df[:31]
    df_plot = df_plot[::-1]

    plt.plot_date(df_plot['date'], df_plot['new_deaths'], linestyle = 'solid')
    plt.xticks(np.arange(0, len(df_plot['date']), 6))
    plt.yticks(np.arange(df_plot['new_deaths'].min(), df_plot['new_deaths'].max(), (int)(df_plot['new_deaths'].max()/20)))
    plt.xlabel('Data')
    plt.ylabel('Nº de mortes')
    plt.title('Gráfico de Nº de mortes diárias no estado de PE')
    plt.show()
    df_plot.to_csv('covid.csv')

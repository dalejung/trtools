import pandas as pd

def parse_table_to_dataframe(table, skip_header=False, columns=None):
    """
        Takes a Beautiful Soup table and creates a dataframe
    """
    rows = table.find_all("tr")

    if not skip_header:
        header = rows[0]
        rows = rows[1:]

    if columns is None:
        cols = header.findAll("th")
        columns = [col.get_text() for col in cols]

    data = []
    for tr in rows:
        cols = tr.findAll("td")
        data.append([col.get_text() for col in cols])

    return pd.DataFrame(data, columns=columns)

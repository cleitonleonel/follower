import os
import json
import string
import numpy as np
import pandas as pd
from datetime import datetime


def format_col_width(ws, rows, cols):
    for index, col in enumerate(cols):
        for item in rows:
            letter = list(string.ascii_uppercase)[index]
            ws.column_dimensions[letter].width = len(item[index]) + 5


def export_to_excel(file_name, data_frame, cols):
    file_path = os.path.join(".", f'{file_name}.xlsx')
    df = pd.DataFrame(data_frame, columns=cols)
    if not os.path.exists(file_path):
        df.to_excel(file_path, header=False, index=False)
    with pd.ExcelWriter(file_path, mode='a', if_sheet_exists='overlay') as writer:
        df.to_excel(writer, startrow=writer.sheets['Sheet1'].max_row, header=False, index=False)
        worksheet = writer.sheets['Sheet1']
        format_col_width(worksheet, data_frame, cols)
        writer.save()


def report_save(report_type, data, data_type):
    filename = f"report-{data_type}-{datetime.now().strftime('%Y-%m-%d')}"
    if report_type == "json":
        with open(os.path.join(".", f"{filename}.json"), "a") as report_json:
            report_json.write(json.dumps(data, indent=4))
    elif report_type == "excel":
        cols = [list(item["object"].keys()) for item in data][0]
        rows = np.array([list(item["object"].values()) for item in data])
        export_to_excel(f"{filename}", rows, cols)
    elif report_type == "csv":
        cols = [list(item["object"].keys()) for item in data][0]
        data_rows = {item: [list(item["object"].values())[index] for item in data]
                     for index, item in enumerate(cols)}
        df = pd.DataFrame(data_rows, columns=cols)
        df.to_csv(os.path.join(".", fr"{filename}"), mode="a", index=False, header=True)

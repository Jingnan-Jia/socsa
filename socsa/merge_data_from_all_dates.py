import csv
import glob
import os
import shutil
from distutils.dir_util import copy_tree
from collections import OrderedDict

import pandas as pd
# import streamlit as st
from tqdm import tqdm
import numpy as np
import datetime

from typing import List, Sequence, Dict


def ordered_dates(data_dir: str) -> List[str]:
    ex_dirs = [f.name for f in os.scandir(data_dir) if f.is_dir()]
    ex_abs_dirs = [f.path for f in os.scandir(data_dir) if f.is_dir()]

    f = "%Y-%m-%d"
    dates = [datetime.datetime.strptime(date, f).date() for date in ex_dirs]
    dates, ex_abs_dirs = zip(*sorted(zip(dates, ex_abs_dirs)))
    # dates = sorted(dates)
    # dates = [str(date) for date in dates]
    # ex_dirs = [os.path.join(data_dir, date) for date in dates]
    return ex_abs_dirs

def get_date_data_dt(date_dirs: Sequence[str]) -> Dict[str, List[str]]:
    date_data_dt = OrderedDict()
    for date_dir in date_dirs:
        # ex_dates = [f.name for f in os.scandir(date_dir) if f.name.split('_')[-1]=='data.txt']  # find data file
        ex_dates = [f.path for f in os.scandir(date_dir) if f.name.split('_')[-1]=='data.txt']  # find data file
        ex_dates = [f for f in ex_dates if 'dark' not in f]  # exclude dark files
        ex_dates = [[os.path.basename(f).split("_")[0], os.path.basename(f).split("_data")[0].split("_")[-1], f] for f in ex_dates]
        date_data_dt[os.path.basename(date_dir)] = ex_dates
    return date_data_dt


def get_pre_post_ls(date_data_dt):
    pre_set, post_set = set(), set()
    for key, date_data in date_data_dt.items():
        for pre, post, file in date_data:
            pre_set.add(pre)
            post_set.add(post)
    pre_ls = list(pre_set)
    pre_ls_nb = [int(pre) for pre in pre_ls]
    pre_ls_nb, pre_ls = zip(*sorted(zip(pre_ls_nb, pre_ls)))  # sort the list

    post_ls = list(post_set)
    post_ls_nb = [int(post) for post in post_ls]
    post_ls_nb, post_ls = zip(*sorted(zip(post_ls_nb, post_ls)))  # sort the list
    
    return pre_ls, post_ls

def get_file(pre, post, data_ls):
    for ls in data_ls:
        if ls[0]==pre and ls[1] == post:
            return ls[-1]
    raise FileNotFoundError(f"找不到该文件： 前缀是{pre}, 后缀是{post}")


if __name__ == "__main__":
    """ This file is used to merge data information from all dates. we first proposed this idea and implemented it on
    2021-06-30.
    """
    abs_dir_path = os.path.dirname(os.path.realpath(__file__))  # abosolute path of the current .py file
    data_dir: str = os.path.join(abs_dir_path, "data", "Shelf lifetime")
    post_dir = os.path.join(data_dir, "postprocessing")
    if os.path.isdir(post_dir):
        shutil.rmtree(post_dir)

    date_dirs: List[str] = ordered_dates(data_dir)
    date_data_dt: Dict[str, List[str]] = get_date_data_dt(date_dirs)
    pre_ls, post_ls = get_pre_post_ls(date_data_dt)

    os.mkdir(post_dir)
    for pre in pre_ls:
        out_file = os.path.join(post_dir, pre+'.xlsx')
        for post in post_ls:
            sheet = pd.DataFrame()
            for i, (date, data_ls) in enumerate(date_data_dt.items()):
                sheet.at[i, 'date'] = date
                try:
                    file = get_file(pre, post, data_ls)
                    df = pd.read_csv(file, names=['key', 'value'], index_col=0, delimiter="\t")  # 打开该文件
                    sheet.at[i, "Jsc (mAcm-2)"] = df.at["Jsc (mAcm-2):", 'value'] # first element in this series (only 1)
                    sheet.at[i, "Voc (V)"] = df.at["Voc (V):", 'value']
                    sheet.at[i, "Fill Factor"] = df.at["Fill Factor:", 'value']
                    sheet.at[i, "Power Conversion Efficiency (%)"] = df.at["Power Conversion Efficiency (%):", 'value']
                except FileNotFoundError:
                    print(f"找不到该文件：日期是{date}, 前缀是{pre}, 后缀是{post}")
                    continue
            sheet.set_index('date', inplace=True)
            if not os.path.isfile(out_file):
                with pd.ExcelWriter(out_file) as writer:  # create a file or overwrite the original files
                    sheet.to_excel(writer, sheet_name='Pixel_' + str(post))
            else:
                with pd.ExcelWriter(out_file, engine="openpyxl", mode='a') as writer:
                    sheet.to_excel(writer, sheet_name='Pixel_' + str(post))
    print("finish !")





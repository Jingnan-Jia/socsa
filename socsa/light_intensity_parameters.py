# -*- coding: utf-8 -*-
# @Time    : 3/3/21 12:25 PM
# @Author  : Jingnan
# @Email   : jiajingnan2222@gmail.com
import csv
import glob
import os

import pandas as pd
# import streamlit as st
from tqdm import tqdm


def search_files(data_dir, cell, prefix):
    data_files = sorted(glob.glob(os.path.join(data_dir, "*" + str(cell) + "_" + prefix)))
    light_intensity_ls = [os.path.basename(data_file).split("_")[0] for data_file in data_files]
    intensity_dict = {}
    for intensity, data_file in zip(light_intensity_ls, data_files):
        intensity_dict[intensity] = data_file

    intensity_int_dict = {}
    for intensity in light_intensity_ls:
        if "dark" in intensity:
            continue
        if "-" in intensity:
            raise Exception(f"intensity文件包含‘-’，请删除此文件: {intensity}")
            # try:
            #     if use_second_test:
            #         intensity_int_dict[float(intensity.split("-")[0])] = intensity_dict[intensity]
            #
            #         intensity_dict.pop(intensity.split("-")[0])
            #     else:
            #         intensity_int_dict[float(intensity.split("-")[0])] = intensity_dict[intensity]
            #
            #         intensity_dict.pop(intensity)
            # except KeyError:
            #     pass
        else:
            try:
                intensity_int_dict[float(intensity)] = intensity_dict[intensity]
            except KeyError:
                pass

    data_files = []
    intesity_int_ls = []
    for intensity, data_file in intensity_int_dict.items():
        intesity_int_ls.append(intensity)
        data_files.append(data_file)

    try:
        light_intensity_ls, data_files = zip(*sorted(zip(intesity_int_ls, data_files)))
    except ValueError:
        light_intensity_ls, data_files = [], []

    return light_intensity_ls, data_files

def reorganize_data(device_ids, father_dir, targt_dir):
    for device_id in device_ids:
        fpath = os.path.join(father_dir, device_id)

        out_file = os.path.join(targt_dir, device_id+ "_data.xlsx")

        data_ls = []
        cells = [1]
        for idx, cell in enumerate(cells):
            light_intensity_ls, data_files = search_files(data_dir=fpath, cell=cell, prefix="data.txt")
            if len(light_intensity_ls)==0:
                data_np = pd.DataFrame()
                data_ls.append(data_np)
                continue  # pass this iteration
            multi_data_dict = {}
            for data_file in tqdm(data_files):
                data = pd.read_csv(data_file, header=None)
                base_name = os.path.basename(data_file)
                light_intensity = base_name.split("_")[0]

                single_data_dict = {"File name": base_name,
                                    "light intensity": light_intensity}
                with open(data_file) as csvfile:
                    reader = csv.reader(csvfile, delimiter='\t')
                    for row in reader:
                        single_data_dict[row[0]] = row[1]

                if len(multi_data_dict) == 0:  # empty dict
                    for key, value in single_data_dict.items():
                        multi_data_dict[key] = [single_data_dict[key]]  # put it into a list
                else:
                    for key, value in single_data_dict.items():
                        multi_data_dict[key].append(value)

            data_np = pd.DataFrame.from_dict(multi_data_dict)
            data_ls.append(data_np)

        idx = 0
        for cell, data_np in zip(cells, data_ls):
            if not os.path.isfile(out_file) or idx==0:
                with pd.ExcelWriter(out_file) as writer:
                    data_np.to_excel(writer, sheet_name='Cell_' + str(cell))
                    # writer.save()
            else:
                with pd.ExcelWriter(out_file, engine="openpyxl", mode='a') as writer:
                    data_np.to_excel(writer, sheet_name='Cell_' + str(cell))
                    # writer.save()
            print("output data to ", out_file, 'Cell_' + str(cell))
            idx += 1


if __name__ == "__main__":
    device_ids = ['60', '62', '75', '75-1', '76', '76-1', '78', '81']
    abs_dir_path = os.path.dirname(os.path.realpath(__file__))  # abosolute path of the current .py file
    father_dir = abs_dir_path  + "\\data\\Light intensity-5.5 test"
    reorganize_data(device_ids, father_dir)

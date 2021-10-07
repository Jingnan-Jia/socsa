# -*- coding: utf-8 -*-
# @Time    : 3/3/21 12:25 PM
# @Author  : Jingnan
# @Email   : jiajingnan2222@gmail.com
import csv
import glob
import os
import shutil
from distutils.dir_util import copy_tree

import pandas as pd
# import streamlit as st
from tqdm import tqdm
from socsa.light_intensity_parameters import search_files
import numpy as np


def calculate_v0(x_1, x_2, y_1, y_1_dark, y_2, y_2_dark):
    a = y_1 - y_1_dark
    b = x_2 - x_1
    c = y_2_dark - y_1_dark
    d = y_2 - y_1

    x = a * b / (c - d) + x_1
    # y = d / b * (x - x_1) + y_1
    return x


def find_min_idx(diff_series, out_file: str) -> int:
    out_file = out_file.split('after_processing')[-1]
    diff_np = np.array(diff_series)
    for idx, i in enumerate(diff_np):
        if i < 0:
            if idx == 0:
                # raise Exception("first diff value is negtive")
                print("第一个暗电流就大于测试电流: " + out_file)
                avail = 'skip'
                return idx, avail
            else:
                avail = 'normal'
                return idx, avail
    print('没有交叉点，取最小值吧: ' + out_file)
    min_idx = np.argmin(diff_np)
    avail = 'exect'
    return min_idx, avail
    # raise Exception('No crossing point at all')


def get_idxmin(ref_value, target):
    diff = target - ref_value
    diff_abs = diff.abs()
    idxmin = diff_abs.idxmin()
    return idxmin


def argmin_positive(data: pd.Series):
    data = np.array(data)
    data[data < 0] = 10000
    return np.argmin(data)


def jv(ex_ids, data_dir, target_dir):
    """
    Main function to get jv.
    Args:
        ex_ids: experiment IDs in this batch of data
        data_dir: directory of this batch of data
        target_dir: directory to save the post-processing data

    Returns:
        None.

    Examples:
        >>> abs_dir_path = os.path.dirname(os.path.realpath(__file__))
        >>> source_dir = os.path.join(abs_dir_path, "data", "Light intensity-5.5 test")
        >>> device_ids = ['60', '62', '75']
        >>> target_dir = os.path.join(source_dir, "after_processing")
        >>> jv(device_ids, source_dir, target_dir)

    """
    for ex_id in ex_ids:  # 对每一组实验都进行如下操作
        print("实验序号: ", ex_id)  # 打印一下电池序号
        print("=============")
        fpath = os.path.join(data_dir, ex_id)  # 获取此次实验数据的存储的文件夹
        dir_ex_id = os.path.join(target_dir, ex_id)  # 将来生成新的数据的文件夹
        if not os.path.isdir(dir_ex_id):
            os.makedirs(dir_ex_id)
        copy_tree(fpath, dir_ex_id)  # 先把原始数据都复制到新的文件夹下
        # （接下来，其中'*_data.txt'文件将被保留不变，而其他文件将会被从第四象限转到第一象后覆盖。)
        out_summary_file = os.path.join(target_dir, ex_id + "jv_summary.xlsx")  # 输出的summary文件名称
        data_ls = []  # 这个空列表将来存放测试结果
        v0_ds = []  # 这个空列表将来存放V0
        cells = [1, 2, 3, 4, 5, 6]  # 6个电池

        for idx, cell in enumerate(cells):  # 对于每一个电池，执行如下操作
            # 处理dark测试结果
            dark_file = glob.glob(os.path.join(fpath, '*dark*' + str(cell) + ".txt")) # 提取该电池的所有dark测试结果
            if len(dark_file) == 0:  # 如果该电池不存在Dark测试结果
                print(f"第{ex_id}个实验的第{cell}号电池缺少文件名包含dark的文件")
                data_ls.append(pd.DataFrame())  # 该电池的测试数据为空
                v0_ds.append(pd.DataFrame())  # 该电池的V0为空
                continue  # 跳过后面的步骤，直接去看下一个电池
                # raise Exception(f"第{ex_id}个实验的第{cell}号电池缺少文件名包含dark的文件")
                # dark_file = glob.glob(os.path.join(fpath, 'dark-1_100_' + str(cell) + ".txt"))
            elif len(dark_file) > 1:  # 如果该电池有不止一个Dark测试结果， 就报错！
                raise Exception(f"第{cell}号电池文件名包含dark的文件不止一个，请删除多余的dark文件再运行，目前的dark文件有：{dark_file}")

            dark_file = dark_file[0]  # 提取第一个dark文件名称（其实也就只有这一个）
            dark = pd.read_csv(dark_file, delimiter="\t")  # 读取这个dark文件
            del dark["Measured Current /A"]  # 删除中间列
            # 电流这列（原来的第三列）取相反数，新建一列，命名为“第一象限的电流”
            dark["Current Density /mAcm-2 in first quadrant"] = - dark["Current Density /mAcm-2"]
            del dark["Current Density /mAcm-2"]  # 删除就到第四象限的电流列


            # 处理不同光强的测试结果
            print("电池序号: ", cell)  # 打印一下电池序号
            # 搜索该电池的所有测试结果，以data.txt为后缀
            light_intensity_ls, data_files = search_files(data_dir=fpath, cell=cell, prefix="data.txt")
            data_files = [file[:-9] + ".txt" for file in data_files]  # 把这些文件名后缀中的data去掉，得到测试数据的文件名称
            # print(data_files)
            # print("---------")
            sheet_df = pd.DataFrame()  # 新建一个空表单，用于存储所有的光强和电流
            sheet_v0 = pd.DataFrame()  # 新建一个空表单，用于存储所有光强和对应的的V0
            for data_file in data_files:  # 对于每一个光强对应的测试结果，进行如下操作
                data = pd.read_csv(data_file, delimiter="\t")  # 读取该电池下，该光强的测试结果
                del data["Measured Current /A"]  # 删除中间列
                data["Current Density /mAcm-2 in first quadrant"] = - data["Current Density /mAcm-2"]  # 转换到第一象限
                del data["Current Density /mAcm-2"]  # 删除第四象限列
                out_file = os.path.join(dir_ex_id, os.path.basename(data_file))  # 输出文件名，用于存储转换到第一象限后的测试结果
                data.to_csv(out_file, index=None, sep='\t')  # 存储到新的路径

                df_all = pd.DataFrame()  # 新建一个空的表单，用于存储此光强下的数据处理结果
                df_all["diff"] = data["Current Density /mAcm-2 in first quadrant"] -\
                                 dark["Current Density /mAcm-2 in first quadrant"]  # 正光强下的电流减去dark电流（第一象限）
                df_all["diff_abs"] = df_all["diff"].abs()  # 取绝对值，用于寻找交点

                df_all["Voltage /V"] = dark["Voltage /V"]  # 电压值（dark的电压和正光强下的电压是一样的，所以随便用谁的都行）
                # 下面是正光强下的电流和dark下的电流
                df_all["Dark Current Density /mAcm-2 in first quadrant"] = dark["Current Density /mAcm-2 in first quadrant"]
                df_all["Current Density /mAcm-2 in first quadrant"] = data["Current Density /mAcm-2 in first quadrant"]


                # min_idx = df_all["diff_abs"].idxmin()

                df_all = df_all[::-1].reset_index(drop=True)  # 调转顺序，来求V0
                min_idx, avail = find_min_idx(df_all['diff'], out_file)
                if avail == 'skip':
                    continue
                elif avail=='exect':
                    V0 = df_all["Voltage /V"][min_idx]
                elif avail=='normal':

                    if df_all["diff_abs"][min_idx] == 0:  # 如果绝对值最小值刚好为0，那它就是交点，V0就是电流绝对值为0所对应的电压值
                        V0 = df_all["Voltage /V"][min_idx]
                    else:
                        if df_all["diff"][min_idx] > 0: # 如果电流绝对值的最小值大于0，那么需要找到紧跟着它的那个点，用于计算交点坐标
                            x_first = min_idx
                            x_second = x_first + 1
                            if x_second == len(df_all):
                                x_first -= 1
                                x_second -= 1
                        else:  # 如果电流绝对值的最小值小于0，那么需要找到它前面的那个点，用于计算交点坐标
                            x_second = min_idx
                            x_first = x_second - 1
                            if x_first < 0:
                                x_first += 1
                                x_second += 1

                        y_first = df_all["Current Density /mAcm-2 in first quadrant"][x_first]
                        y_first_dark = df_all["Dark Current Density /mAcm-2 in first quadrant"][x_first]
                        y_second = df_all["Current Density /mAcm-2 in first quadrant"][x_second]
                        y_second_dark = df_all["Dark Current Density /mAcm-2 in first quadrant"][x_second]
                        V0 = calculate_v0(df_all['Voltage /V'][x_first],
                                          df_all['Voltage /V'][x_second],
                                          y_first, y_first_dark, y_second, y_second_dark )
                else:
                    raise Exception('wrong avail flag')
                df_all = df_all[::-1].reset_index(drop=True)  # 求出V0之后，顺序再调整回来

                x_axis = V0 - df_all["Voltage /V"]  # 新 的x列
                y_axis = df_all["Current Density /mAcm-2 in first quadrant"] - \
                         df_all["Dark Current Density /mAcm-2 in first quadrant"]  # 新的y列

                intensity = os.path.basename(data_file).split("_")[0]  # 从文件名中提取光强数据，例如：0.001

                sheet_v0 = sheet_v0.append({"intensity": intensity, "V0": V0}, ignore_index=True)

                sheet_df[intensity + "_x"] = x_axis  # 把这一列x放到表单里
                sheet_df[intensity + "_y"] = y_axis  # 把这一列y放到表单里

            # 现在都表单里已经存放了所有光强下的x和y，接下来需要增加这么几列：
            # 1. 所有光强从大到小排
            # 2. 开路情况下，所有光强对应的x, y
            # 3. 短路情况下，所有光强对应的x, y
            # 4. 功率最大情况下，所有光强对应的x, y

            file_100_intensity = glob.glob(os.path.join(dir_ex_id, "100*" + str(cell) + ".txt"))  # 光强为100时候该电池的测试数据
            if len(file_100_intensity):  # 如果此文件存在的话
                file_100_intensity = file_100_intensity[0]
                df = pd.read_csv(file_100_intensity, delimiter="\t")  # 打开该文件
                power_series = df.iloc[:,0] * df.iloc[:,1]  # 电压乘以电流得到功率power

                # 1. 所有光强从大到小排
                tmp_ls = []  # 准备往里面放光强的字符形
                for inten in light_intensity_ls:  #准备对排序后的光强转换成字符，顺序保持从小到大
                    if inten % 1 ==0:  # 如果是整数，就先int一下再转，不然会有2.0这种情况。
                        tmp_ls.append(str(int(inten)))
                    else:  # 如果是小数，就直接转成字符
                        tmp_ls.append(str(inten))
                intensity_df = pd.Series(tmp_ls)  # 所有光强成为一列

                # 2. 开路情况下，所有光强对应的x, y

                idxmin_ye0 = argmin_positive(df["Voltage /V"])# 100光强下，电压绝对值为0时候的x提取出来，代表开路open circuit
                # idxmin_ye0 = df["Voltage /V"].abs().idxmin()
                x1_voltage_equal_0 = []
                y1_voltage_equal_0 = []

                ref_x = sheet_df[str(100) + "_x"].iat[idxmin_ye0]
                for intens in tmp_ls:
                    try:
                        if intens == 100:
                            idxmin = idxmin_ye0
                        else:
                            idxmin = get_idxmin(ref_value=ref_x, target=sheet_df[str(intens) + "_x"])

                        x1 = sheet_df[str(intens)+"_x"].iat[idxmin]
                        y = sheet_df[str(intens)+"_y"].iat[idxmin]
                        x1_voltage_equal_0.append(x1)
                        y1_voltage_equal_0.append(y)
                    except KeyError:
                        continue

                x1_voltage_equal_0 = pd.Series(x1_voltage_equal_0)
                y1_voltage_equal_0 = pd.Series(y1_voltage_equal_0)

                # 3. 短路情况下，所有光强对应的x, y
                idxmin_ye0_2 = argmin_positive(df["Current Density /mAcm-2 in first quadrant"])
                # idxmin_ye0_2 = df["Current Density /mAcm-2 in first quadrant"].abs().idxmin()
                # 100光强下，电流绝对值为0的x提取出来,代表短路
                x2_current_equal_0 = []
                y2_current_equal_0 = []
                ref_x = sheet_df[str(100) + "_x"].iat[idxmin_ye0_2]
                for intens in tmp_ls:
                    try:
                        if intens==100:
                            idxmin = idxmin_ye0_2
                        else:
                            idxmin = get_idxmin(ref_value=ref_x, target=sheet_df[str(intens) + "_x"])
                        x2 = sheet_df[str(intens) + "_x"].iat[idxmin]
                        y2 = sheet_df[str(intens) + "_y"].iat[idxmin]
                        x2_current_equal_0.append(x2)
                        y2_current_equal_0.append(y2)
                    except KeyError:
                        continue
                x2_current_equal_0 = pd.Series(x2_current_equal_0)
                y2_current_equal_0 = pd.Series(y2_current_equal_0)

                # corredted_idxmin_ye0_2 = df["Current Density /mAcm-2 in first quadrant"].abs().idxmin()
                # # 100光强下，电流绝对值为0的x提取出来,代表短路
                # corredted_flag = 1  # 下面是对已经取得的开路和短路数据进行矫正过程， 保证从光强19开始， y得是正数
                # while corredted_flag:
                #     try:
                #         y19 = sheet_df[str(19) + "_y"].iat[corredted_idxmin_ye0_2]
                #         if y19 < 0:
                #             print(f"实验号：{ex_id}, 电池号： {cell}， 光强19时候电流是负数，需要进行矫正，向下取一个数")
                #             corredted_idxmin_ye0_2 += 1
                #         else:
                #             corredted_flag = 0
                #     except KeyError:
                #         break
                #
                # if corredted_idxmin_ye0_2 != idxmin_ye0_2:
                #     x2_current_equal_0_corrected = []
                #     y2_current_equal_0_corrected = []
                #     for intens in tmp_ls:
                #         x2 = sheet_df[str(intens) + "_x"].iat[corredted_idxmin_ye0_2]
                #         y2 = sheet_df[str(intens) + "_y"].iat[corredted_idxmin_ye0_2]
                #
                #         x2_current_equal_0_corrected.append(x2)
                #         y2_current_equal_0_corrected.append(y2)
                #     x2_current_equal_0_corrected = pd.Series(x2_current_equal_0_corrected)
                #     y2_current_equal_0_corrected = pd.Series(y2_current_equal_0_corrected)

                # 4. 功率最大情况下，所有光强对应的x, y
                idxmin_ye0_3 = power_series.idxmax()  # 光强为100时候，功率最大的时候。
                x3_power_max = []
                y3_power_max = []
                ref_x = sheet_df[str(100) + "_x"].iat[idxmin_ye0_3]
                for intens in tmp_ls:
                    try:
                        if intens == 100:
                            idxmin = idxmin_ye0_2
                        else:
                            idxmin = get_idxmin(ref_value=ref_x, target=sheet_df[str(intens) + "_x"])

                    # for intens in tmp_ls:
                        x3 = sheet_df[str(intens) + "_x"].iat[idxmin]
                        y3 = sheet_df[str(intens) + "_y"].iat[idxmin]
                        x3_power_max.append(x3)
                        y3_power_max.append(y3)
                    except KeyError:
                        continue
                x3_power_max = pd.Series(x3_power_max)
                y3_power_max = pd.Series(y3_power_max)

                sheet_df = pd.concat([sheet_df, df, power_series.rename("Power"), sheet_v0['intensity'].rename("intensity"),
                                      x1_voltage_equal_0.rename("open_circuit_x"),
                                      y1_voltage_equal_0.rename("open_circuit_y"),
                                      x2_current_equal_0.rename("short_circuit_x"),
                                      y2_current_equal_0.rename("short_circuit_y"),
                                      x3_power_max.rename("power_max_x"),
                                     y3_power_max.rename("power_max_y")], axis=1)
                # if corredted_idxmin_ye0_2 != idxmin_ye0_2:
                #     sheet_df = pd.concat([sheet_df, x2_current_equal_0_corrected.rename("short_circuit_x_corrected"),
                #                           y2_current_equal_0_corrected.rename("short_circuit_y_corrected")], axis=1)

                # appended_df.rename(columns={df.columns[]: "Power", df.columns[31]:"Intensity"}, inplace=True)
            # 把这几个表单放到一个列表中，将来保存为一个excel文件
            data_ls.append(sheet_df)
            v0_ds.append(sheet_v0)

        for idx, (cell, data_np, v0) in enumerate(zip(cells, data_ls, v0_ds)):
            if not os.path.isfile(out_summary_file) or idx == 0:
                with pd.ExcelWriter(out_summary_file) as writer:  # create a file or overwrite the original files
                    data_np.to_excel(writer, sheet_name='Cell_' + str(cell))
                    v0.to_excel(writer, sheet_name='Cell_' + str(cell) + "V0")
            else:
                with pd.ExcelWriter(out_summary_file, engine="openpyxl", mode='a') as writer:
                    data_np.to_excel(writer, sheet_name='Cell_' + str(cell))
                    v0.to_excel(writer, sheet_name='Cell_' + str(cell) + "V0")
            # print("output data to ", out_summary_file, 'Cell_' + str(cell))

if __name__ == "__main__":
    abs_dir_path = os.path.dirname(os.path.realpath(__file__))  # abosolute path of the current .py file
    data_dir = os.path.join(abs_dir_path,"Light intensity-5.5 test")
    ex_ids = ['60', '62', '75', '75-1', '76', '76-1', '78', '81']
    jv(ex_ids, data_dir)
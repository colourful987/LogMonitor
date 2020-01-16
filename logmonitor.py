#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: pmst
# Brief:  Simple implementation of search keyword in monitor log file,
#         provide report error message to your server

import sys
import os
import re
import configparser
import socket
import datetime
import threading


def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip


workspace = os.path.dirname(os.path.realpath(sys.argv[0]))
conf_file_path = os.path.join(workspace, "monitoritems.conf")
host_ip = get_host_ip()


class LogFileDiagnosis(object):
    """
        日志文件诊断器，目前配置文件描述监控一个日志文件，多个关键字监控
        更多请见配置中的item选项，定义了keyword关键字，阈值，等级和描述
    """

    def __init__(self, logfile_path, items: dict):
        self.logfile_path = logfile_path
        self.tmp_file = os.path.join('/tmp', self.logfile_path.replace('/', '') + '_st_size.tmp')
        self.last_logfile_size = self.__read_last_logfile_content_size()
        self.monitor_items = items
        self.res = {}

    def __record_current_logfile_content_size(self, size):
        with open(self.tmp_file, 'w') as f:
            f.write(str(size))

    def __read_last_logfile_content_size(self):
        """
            从缓存文件中读取上一次日志文件内容大小X，当前文件内容大小为Y，
            所以本地诊断范围是[X, Y].
        :return: 上一次读入的日志文件内容大小
        """
        if os.path.exists(self.tmp_file):
            with open(self.tmp_file, 'r') as f:
                pre_size = f.read()
                pre_size.replace('\n', '')
                pre_size = int(pre_size)
                return pre_size
        else:
            return 0

    def diagnosis(self):
        if not os.path.exists(self.logfile_path):
            print('配置文件中要监控的日志文件不存在')
            return None

        # 读入要分析的日志文件
        with open(self.logfile_path, 'r') as file:
            # 获取文件的状态描述
            file_stats = os.stat(self.logfile_path)
            current_size = file_stats[6]
            offset = self.last_logfile_size
            if current_size == self.last_logfile_size:
                print("日志未发生变化，无需诊断错误日志。")
                return None
            elif current_size < self.last_logfile_size:
                print("日志可能存在变更，将重新全面分析。")
                offset = 0
            else:
                print("日志开始读取位置：{}，总计要读：{}".format(offset, current_size - offset))

            # 记录当前文件的位置
            self.__record_current_logfile_content_size(current_size)
            # 定位内容游标卡尺到offset位置读取文件内容，直至 current_size 位置
            file.seek(offset)
            content = file.read()
            content = content.replace('\n', '')

        # 生成正则匹配表达式
        if len(self.monitor_items) > 0:
            for key, value in self.monitor_items.items():
                keyword = value['keyword']
                pattern = re.compile(keyword)
                find_res = pattern.findall(content)
                if len(find_res) > 0:
                    desc = "监控到 {0} 情况，已触发 {1} 次".format(value["description"], len(find_res))
                    self.res[keyword] = desc
                # else:
                #     print("关键字：{} 未触发".format(keyword))
        if len(self.res) == 0:
            return None

        return self.res


class MyParser(configparser.ConfigParser):
    def as_dict(self):
        d = dict(self._sections)
        for k in d:
            d[k] = dict(d[k])
        return d


def logfile_diagnosis_handler():
    # 配置文件读取
    conf = MyParser()
    conf.read(conf_file_path)

    log_file_path = conf.get("DEFAULT", "log_file_path")
    monitor_interval = conf.get("DEFAULT", "monitor_interval")

    diagnosis = LogFileDiagnosis(log_file_path, conf.as_dict())
    res = diagnosis.diagnosis()
    date = datetime.datetime.now()
    if res is not None:
        print("{} : 主机 {} 预警，内容如下：{}".format(date, host_ip, res))
    else:
        print("{} : 一切如常。".format(date))

    timer = threading.Timer(monitor_interval, logfile_diagnosis_handler)  # 5分钟执行一次
    timer.start()


if __name__ == '__main__':
    # 检查配置文件
    if not os.path.exists(conf_file_path):
        print('配置文件不存在')
        exit(0)

    # 5.开启子线程监听设备状态
    monitor_thread = threading.Thread(target=logfile_diagnosis_handler)
    monitor_thread.start()
    monitor_thread.join()

    print("开始监听...")
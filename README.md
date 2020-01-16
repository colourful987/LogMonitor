# LogMonitor
monitor specified log file, if occured keywords you setting, sendmail or other method to report. 

# How to use

在当前目录下新建一个 *monitoritems.conf* 配置文件，内容按照下面规范添加。可自行修改脚本动态配置。

```angular2
[DEFAULT]
# 监控日志路径
log_file_path=/path/to/logfile
# 监控频率，每 x 秒触发一次
monitor_interval=60

[item1]
# 监控关键字(不要加引号，可传入正则表达式)
keyword =Unable to send to CLOSED client
# 阈值
threshold = 1
# 等级
level = info
# 描述
description = 报警关键字对应的描述信息

[item2]
# 监控关键字(不要加引号，可传入正则表达式)
keyword = 其他关键字或者正则表达式
# 阈值
threshold = 2
# 等级
level = error
# 描述
description = 报警关键字对应的描述信息
```
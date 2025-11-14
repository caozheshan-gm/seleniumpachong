# seleniumpachong
用于企查查的selenium爬虫

简介：
此爬虫为前端爬虫，效率较低，但不容易被检测到，用于企查查官网，2025年1月还能正常使用。

文件介绍：
getEname.py ：在代码中companies_to_search部分添加公司列表字符如['xxx','xxx','xxx']，可以返回文件包含了公司的英文名称与业务范围。
getrelation.py：同上，返回公司的疑似关联公司。
shaixuan.py：配合getEname.py生成的结果使用，需要配置语言大模型，根据公司业务范围和关键词来判断该公司是否属于xxx行业。我使用的是deepseek r1 1.58bit模型，由于r1模型会先思考啰嗦一大堆，效率较低，但是准确率很高。

使用方法：
使用前需要先Windows+R, 输入：msedge --remote-debugging-port=9222 --user-data-dir="C:\EdgeProfile"，启动edge调试，然后再启动程序。
第一次登录企查查需要先扫码。

tips:
没有配置应对验证码的方法。
可以改变代码中的sleep_time和small_sleep来提高爬虫效率。

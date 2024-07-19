from pydantic import BaseModel,field_validator
from typing import Union
from nonebot import get_plugin_config
ALL_GROUPS = False
HOUR = 8
MINUTE = 0
DATA={}
PROVINCES=["北京"]
character=str.maketrans("：", ":")


class Config(BaseModel):
    all_qq_groups: bool = False  
    qq_groups: list[int] = [] 
    qq_friends: list[int] = [] 
    provinces: list[str] = []
    send_time: Union[str, list] = None 


plugin_config = get_plugin_config(Config)

if isinstance(plugin_config.send_time, str):
    plugin_config.send_time= plugin_config.send_time.translate(character)
    HOUR, MINUTE = plugin_config.send_time.split(':')

PROVINCES = plugin_config.provinces


for group in plugin_config.qq_groups:
    DATA.setdefault(
        "G{}".format(group),
        {
            "hour": HOUR,
            "minute": MINUTE,
            "provinces":PROVINCES
        })


for friend in plugin_config.qq_friends:
    DATA.setdefault(
        "F{}".format(friend),
        {
            "hour": HOUR,
            "minute": MINUTE,
            "provinces":PROVINCES
        })
    
PROVINCES_ID = {
    "安徽": 340000,
    "澳门": 820000,
    "北京": 110000,
    "重庆": 500000,
    "福建": 350000,
    "广东": 440000,
    "广西": 450000,
    "贵州": 520000,
    "甘肃": 620000,
    "海南": 460000,
    "河南": 410000,
    "湖北": 420000,
    "湖南": 430000,
    "河北": 130000,
    "黑龙江": 230000,
    "江苏": 320000,
    "江西": 360000,
    "吉林": 220000,
    "辽宁": 210000,
    "内蒙古": 150000,
    "宁夏": 640000,
    "青海": 630000,
    "陕西": 610000,
    "四川": 510000,
    "上海": 310000,
    "山西": 140000,
    "山东": 370000,
    "天津": 120000,
    "台湾": 710000,
    "香港": 810000,
    "新疆": 650000,
    "西藏": 540000,
    "云南": 530000,
    "浙江": 330000
}
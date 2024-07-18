from pathlib import Path
import httpx
import json
import re
from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from .config import PROVINCES_ID
DATA_FILE: Path = Path(__file__).parent/"DATA.json"

def get_data(file=DATA_FILE) -> dict:
    if not file.exists():
        return {}
    return json.loads(file.read_text(encoding="utf-8"))


def save_data(data: dict, file=DATA_FILE) -> None:
    file.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")

async def get_group_list(bot: Bot) -> list:
    """获取群聊列表"""
    groups = await bot.call_api("get_group_list", no_cache=True)
    group_list = []
    for group in groups:
         group_list.append(group["group_id"])
    return  group_list


async def get_news_info(provinces:list):
    async with httpx.AsyncClient() as client:
        msg=[]
        if not provinces:
            return MessageSegment.text("省份数据为空")
        for province in provinces:
            url=f'https://www.autohome.com.cn/oil/{PROVINCES_ID[province]}.html'
            response = await client.get(url)
            if response.status_code == 200:
                msg.append(re.search(r'(?<=(<p class="core_description__aT_Rj">)).*?(?=(</p>))', response.text).group(0).replace("<!-- -->",""))
            else:
                msg.append(f"获取{province}油价失败")
        return MessageSegment.text('\n'.join(msg))
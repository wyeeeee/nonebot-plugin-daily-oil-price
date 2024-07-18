import re
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import Arg, CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.typing import T_State
from nonebot import get_bot, get_driver, on_command, require
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    Message,
    MessageEvent
)
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
from .config import Config,ALL_GROUPS,HOUR,MINUTE,DATA,PROVINCES,PROVINCES_ID
from .utils import get_data,save_data,get_group_list,get_news_info
__plugin_meta__ = PluginMetadata(
    name="每日油价",
    description="查询每日地区油价，定时推送油价",
    usage="今日油价",
    type="application",
    homepage="https://github.com/wyeeeee/nonebot-plugin-daily-oil-price",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

driver = get_driver()

@driver.on_bot_connect
async def _(bot: Bot):
    DATA.update(get_data())
    save_data(DATA)
    logger.info(f"daily_oil_all_group: {ALL_GROUPS}")
    logger.info(f"daily_oil_env: {DATA}")
    if ALL_GROUPS:
        for id in get_group_list.keys():
            if "G{}".format(id) not in DATA:
                scheduler.add_job(
                push_send,
                "cron",
                args=[id,PROVINCES],
                id=f"daily_oil_push_{id}",
                replace_existing=True,
                hour=HOUR,
                minute=MINUTE,
            )
                logger.debug(f"daily_oil_scheduler: {id[1:]}-{HOUR}:{MINUTE}")
    for id,data in DATA.items():
        scheduler.add_job(
            push_send,
            "cron",
            args=[id,data["provinces"]],
            id=f"daily_oil_push_{id}",
            replace_existing=True,
            hour=data["hour"],
            minute=data["minute"],
        )
        logger.debug(f"daily_oil_scheduler: {id[1:]}-{data['hour']}:{data['minute']}")

push_matcher = on_command("今日油价", priority=5, block=True)
@push_matcher.handle()
async def _(
    event: MessageEvent,
    matcher: Matcher,
    args: Message = CommandArg()
):
    if args.extract_plain_text():
        matcher.set_arg("local_arg", args)


@push_matcher.got("local_arg", prompt="请输入位置")
async def _(event: MessageEvent,matcher: Matcher, state: T_State,local_arg: Message = Arg()):
    province=""
    if isinstance(event, GroupMessageEvent):
        id = "G{}".format(event.group_id)
    else:
        id = "F{}".format(event.user_id)
    if cmd := local_arg.extract_plain_text():
        if cmd[0:3] in ["黑龙江","内蒙古"]:
            province = cmd[0:3]
        else:
            province = cmd[0:2]
        if province in PROVINCES_ID.keys():
            await push_send(id,[province])
            logger.debug(f"daily_oil: {id}-{province}")
        else:
            await matcher.finish("请输入正确的省份")


push_matcher = on_command("油价推送", priority=5, block=True)
@push_matcher.handle()
async def _(
    event: MessageEvent,
    matcher: Matcher,
    args: Message = CommandArg()
):
    if args.extract_plain_text():
        matcher.set_arg("setting_arg", args)


@push_matcher.got("setting_arg", prompt="输入 状态/取消/设置 来管理推送")
async def _(event: MessageEvent,matcher: Matcher, state: T_State,setting_arg: Message = Arg()):
    state.setdefault("repeat_times", 0)
    if isinstance(event, GroupMessageEvent):
        id = "G{}".format(event.group_id)
    else:
        id = "F{}".format(event.user_id)
    if cmd := setting_arg.extract_plain_text():
        if "状态" in cmd:
            if scheduler.get_job(f"daily_oil_push_{id}"):
                DATA=get_data()
                msg=(
                    f"当前推送时间：{DATA[id]['hour']}:{DATA[id]['minute']}\n推送省份: {','.join(DATA[id]['provinces'])}"
                )
                await matcher.finish(msg)
            else:
                await matcher.finish("未设置推送时间")
        elif "取消" in cmd:
            if  scheduler.get_job(f"daily_oil_push_{id}"):
                scheduler.remove_job(f"daily_oil_push_{id}")
                DATA=get_data()
                DATA.pop(id)
                save_data(DATA)
                await matcher.finish("取消推送成功")
                logger.debug(f"daily_oil_scheduler: {id[1:]}-cancel")
            else:
                await matcher.finish("未设置推送时间")
        elif "设置" in cmd:
            pass
        else:
            await matcher.finish("无效指令")
    else:
        await matcher.finish("请输入指令")


@push_matcher.got("time_arg", prompt="请发送定时推送时间 如 12:00")
async def _(    
    event: MessageEvent,
    matcher: Matcher,
    state: T_State,
    time_arg: Message = Arg()
):
    state.setdefault("repeat_times", 0)
    match = re.search(r"(\d*)[:：](\d*)", time_arg.extract_plain_text())
    if match and match[1] and match[2] and 0<=int(match[1])<24 and 0<=int(match[2])<60:
        hour, minute = int(match[1]), int(match[2])
        DATA=get_data()
        if isinstance(event, GroupMessageEvent):
            id = "G{}".format(event.group_id)
        else:
            id = "F{}".format(event.user_id)
        DATA.update({id : {"hour": hour, "minute": minute, "provinces":PROVINCES}})
        save_data(DATA)

    else:
        state["repeat_times"] += 1
        if state["repeat_times"] >= 3:
            await matcher.finish("错误次数过多,结束时间设置")
        await matcher.reject("设置失败，请输入正确格式")


@push_matcher.got("arg", prompt="请发送省份，多个省份以逗号分割 如 黑龙江,内蒙古")
async def _(event: MessageEvent,matcher: Matcher, state: T_State, arg: Message = Arg()):
    state.setdefault("repeat_times", 0)
    character=str.maketrans("，", ",")
    DATA=get_data()
    if isinstance(event, GroupMessageEvent):
        id = "G{}".format(event.group_id)
    else:
        id = "F{}".format(event.user_id)
    if  provinces:=arg.extract_plain_text().translate(character).split(","):
        if all(province in PROVINCES_ID.keys() for province in provinces):
            DATA[id]["provinces"]=provinces
            scheduler.add_job(
                push_send,
                "cron",
                args=[id,provinces],
                id=f"daily_oil_push_{id}",
                replace_existing=True,
                hour=DATA[id]["hour"],
                minute=DATA[id]["minute"],
            )
            save_data(DATA)
            await matcher.finish("设置成功")
            logger.debug(f"daily_oil_scheduler: {id[1:]}-{DATA[id]['hour']}:{DATA[id]['minute']}-{','.join(DATA[id]['provinces'])}")
    state["repeat_times"] += 1
    if state["repeat_times"] >= 3:
        DATA.pop(id)
        save_data(DATA)
        await matcher.finish("错误次数过多,结束设置")
    await matcher.reject("设置失败，请输入正确格式")


async def push_send(id: str,provinces: list):
    bot = get_bot()
    msg=await get_news_info(provinces)
    if id[0:1]=="G":
        await bot.call_api("send_group_msg", group_id=int(id[1:]), message=msg)
    else:
        await bot.call_api("send_private_msg", user_id=int(id[1:]), message=msg)


    
    
    
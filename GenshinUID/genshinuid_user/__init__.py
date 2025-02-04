from typing import Any, Tuple

from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot import on_regex, on_command
from nonebot.permission import SUPERUSER
from nonebot.params import CommandArg, RegexGroup
from nonebot.adapters.onebot.v11 import (
    PRIVATE_FRIEND,
    Bot,
    Message,
    MessageEvent,
    MessageSegment,
    GroupMessageEvent,
)

from ..config import priority
from .qrlogin import qrcode_login
from .get_ck_help_msg import get_ck_help
from .draw_user_card import get_user_card
from ..genshinuid_meta import register_menu
from ..utils.nonebot2.rule import FullCommand
from ..utils.exception.handle_exception import handle_exception
from .add_ck import deal_ck, get_ck_by_stoken, get_ck_by_all_stoken
from ..utils.db_operation.db_operation import bind_db, delete_db, switch_db

add_cookie = on_command('添加', permission=PRIVATE_FRIEND)
get_ck_msg = on_command(
    '绑定ck说明',
    aliases={'ck帮助', '绑定ck'},
    block=True,
    rule=FullCommand(),
)
bind_info = on_command(
    '绑定信息', priority=priority, block=True, rule=FullCommand()
)
refresh_ck = on_command(
    '刷新CK',
    aliases={'刷新ck', '刷新Ck', '刷新Cookies'},
    priority=priority,
    block=True,
    rule=FullCommand(),
)
refresh_all_ck = on_command(
    '刷新全部CK',
    aliases={'刷新全部ck', '刷新全部Ck', '刷新全部Cookies'},
    priority=priority,
    block=True,
    rule=FullCommand(),
    permission=SUPERUSER,
)
bind = on_regex(
    r'^(绑定|切换|解绑|删除)(uid|UID|mys|MYS)([0-9]+)?$', priority=priority
)
get_qrcode_login = on_command(
    '扫码登录',
    aliases={'扫码登陆', '扫码登入'},
    rule=FullCommand(),
)


@refresh_all_ck.handle()
async def send_refresh_all_ck_msg(
    matcher: Matcher,
):
    logger.info('开始执行[刷新全部CK]')
    im = await get_ck_by_all_stoken()
    if isinstance(im, str):
        await matcher.finish(im)
    await matcher.finish(MessageSegment.image(im))


@refresh_ck.handle()
async def send_refresh_ck_msg(
    event: MessageEvent,
    matcher: Matcher,
):
    logger.info('开始执行[刷新CK]')
    qid = event.user_id
    im = await get_ck_by_stoken(qid)
    if isinstance(im, str):
        await matcher.finish(im)
    await matcher.finish(MessageSegment.image(im))


@get_qrcode_login.handle()
async def send_qrcode_login(
    bot: Bot,
    event: GroupMessageEvent,
    matcher: Matcher,
):
    logger.info('开始执行[扫码登陆]')
    qid = event.user_id
    groupid = event.group_id
    im = await qrcode_login(bot, groupid, qid)
    if not im:
        return
    im = await deal_ck(im, qid)
    await matcher.finish(MessageSegment.image(im))


@bind_info.handle()
@register_menu(
    '绑定状态',
    '绑定信息',
    '查询你绑定UID的绑定和推送状态',
    detail_des=(
        '介绍：\n'
        '查询你绑定的UID列表以及它们的CK、SK绑定状态和推送设置\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>绑定信息</ft>'
    ),
)
async def send_bind_card(
    event: MessageEvent,
    matcher: Matcher,
):
    logger.info('开始执行[查询用户绑定状态]')
    qid = event.user_id
    im = await get_user_card(qid)
    logger.info('[查询用户绑定状态]完成!等待图片发送中...')
    await matcher.finish(MessageSegment.image(im))


@add_cookie.handle()
@handle_exception('Cookie', '校验失败！请输入正确的Cookies！')
@register_menu(
    '绑定CK、SK',
    '添加[CK或SK]',
    '绑定你的Cookies以及Stoken',
    trigger_method='好友私聊指令',
    detail_des=(
        '介绍：\n'
        '绑定你的Cookies以及Stoken\n'
        'Cookies (CK)：米游社Cookies；Stoken (SK)：米哈游通行证Cookies\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>添加</ft><ft color=(0,148,200)>[CK或SK]</ft>'
    ),
)
async def send_add_ck_msg(
    event: MessageEvent, matcher: Matcher, args: Message = CommandArg()
):
    mes = args.extract_plain_text().strip().replace(' ', '')
    qid = event.user_id
    im = await deal_ck(mes, qid)
    if isinstance(im, str):
        await matcher.finish(im)
    await matcher.finish(MessageSegment.image(im))


# 群聊内 绑定uid或者mysid 的命令，会绑定至当前qq号上
@bind.handle()
@handle_exception('绑定ID', '绑定ID异常')
@register_menu(
    '绑定UID',
    '绑定xx',
    '绑定原神UID或米游社UID',
    detail_des=(
        '介绍：\n'
        '绑定原神UID或米游社UID\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>绑定'
        '{uid</ft><ft color=(0,148,200)>[原神UID]</ft>'
        '<ft color=(238,120,0)>|mys</ft><ft color=(0,148,200)>[米游社UID]</ft>'
        '<ft color=(238,120,0)>}</ft>'
    ),
)
@register_menu(
    '解绑UID',
    '解绑xx',
    '解绑原神UID或米游社UID',
    detail_des=(
        '介绍：\n'
        '解绑原神UID或米游社UID\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>{解绑|删除}'
        '{uid</ft><ft color=(0,148,200)>[原神UID]</ft>'
        '<ft color=(238,120,0)>|mys</ft><ft color=(0,148,200)>[米游社UID]</ft>'
        '<ft color=(238,120,0)>}</ft>'
    ),
)
@register_menu(
    '切换UID',
    '切换xx',
    '切换当前原神UID或米游社UID',
    detail_des=(
        '介绍：\n'
        '切换当前原神UID或米游社UID\n'
        '绑定一个UID的情况下无法切换\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>切换'
        '{uid</ft><ft color=(0,148,200)>[原神UID]</ft>'
        '<ft color=(238,120,0)>|mys</ft><ft color=(0,148,200)>[米游社UID]</ft>'
        '<ft color=(238,120,0)>}</ft>'
    ),
)
async def send_link_uid_msg(
    event: MessageEvent, matcher: Matcher, args: Tuple[Any, ...] = RegexGroup()
):
    logger.info('开始执行[绑定/解绑用户信息]')
    logger.info('[绑定/解绑]参数: {}'.format(args))
    qid = event.user_id
    logger.info('[绑定/解绑]UserID: {}'.format(qid))

    if args[0] in ('绑定'):
        if args[2] is None:
            await matcher.finish('请输入正确的uid或者mysid！')

        if args[1] in ('uid', 'UID'):
            im = await bind_db(qid, args[2])
        else:
            im = await bind_db(qid, None, args[2])
    elif args[0] in ('切换'):
        im = await switch_db(qid, args[2])
    else:
        if args[1] in ('uid', 'UID'):
            im = await delete_db(qid, {'UID': args[2]})
        else:
            im = await delete_db(qid, {'MYSID': args[2]})
    await matcher.finish(im, at_sender=True)


@get_ck_msg.handle()
async def send_ck_help(bot: Bot, event: GroupMessageEvent):
    msg_list = await get_ck_help()
    forward_msg = []
    for msg in msg_list:
        forward_msg.append(
            {
                "type": "node",
                "data": {"name": "小冰", "uin": "2854196306", "content": msg},
            }
        )
    await bot.call_api(
        'send_group_forward_msg', group_id=event.group_id, messages=forward_msg
    )

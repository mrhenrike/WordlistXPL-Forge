"""zh.py - Chinese cultural password patterns (pinyin romanization).

Pinyin-romanized names, internet slang, holidays and cultural tokens
common in Chinese passwords. Uses pinyin since most password fields
are ASCII-only.

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

from collections.abc import Generator

from wlf_modules.locales import BaseLocaleEngine, register_engine

_NAMES_PINYIN = [
    "wei","fang","lei","jun","jie","yang","ming","qiang","yong","tao",
    "chao","ping","gang","liang","hua","lin","hong","bo","feng","hao",
    "jian","dong","xin","guang","wen","peng","zhi","long","hai","bin",
    "jing","li","yan","xia","mei","ying","na","yun","lan","ting",
    "xue","min","rui","chen","yu","zi","dan","lian","qian","han",
]

_SURNAMES_PINYIN = [
    "wang","li","zhang","liu","chen","yang","zhao","huang","zhou","wu",
    "xu","sun","hu","zhu","gao","lin","he","guo","ma","luo",
    "liang","song","zheng","xie","han","tang","feng","deng","cao","peng",
]

_SLANG = [
    "niubi","daniu","laoshi","geili","jiayou","woaini","wocao",
    "666","888","520","1314","233","9999","8888","6666",
    "nb","yyds","xswl","awsl","nsdd","dddd","zqsg","dbq",
    "baidu","weixin","wechat","taobao","alipay","douyin","bilibili",
    "tiktok","zhihu","weibo","xiaohongshu","meituan","didi",
]

_CULTURE = [
    "beijing","shanghai","guangzhou","shenzhen","chengdu","hangzhou",
    "wuhan","nanjing","xian","chongqing","tianjin","suzhou",
    "zhongguo","china","zhonghua","longde","dragon","panda",
    "changcheng","greatwall","tiananmen","gugong","forbidden",
    "kongzi","confucius","laozi","sunzi","wushu","kungfu","taiji",
    "cha","tea","jiaozi","baozi","huoguo","hotpot","noodle","dim",
    "alibaba","tencent","huawei","xiaomi","bytedance","oppo","vivo",
    "renminbi","yuan","hongbao","mahjong","weiqi","guzheng",
]

_HOLIDAYS = [
    "chunjie","springfest","yuandan","qingming","duanwu","zhongqiu",
    "guoqing","laodong","yuanxiao","chongyang","dongzhi",
]

_YEARS = ["2020","2021","2022","2023","2024","2025","2026","20","21","22","23","24","25","26"]
_SEPS = ["", "_", ".", "@", "#"]
_SUFFIXES = ["!", "@", "#", "123", "1234", "2024", "2025", "2026"]


@register_engine
class ZHEngine(BaseLocaleEngine):
    locale_code = "zh"
    locale_name = "Chinese (Pinyin)"
    locale_aliases = ["zh_cn", "zh_tw", "chinese", "mandarin", "pinyin"]

    def generate(self) -> Generator[tuple[str, float], None, None]:
        seen: set[str] = set()
        count = [0]
        for block, score in [
            (_NAMES_PINYIN, 0.7), (_SURNAMES_PINYIN, 0.6),
            (_SLANG, 0.6), (_CULTURE, 0.6), (_HOLIDAYS, 0.5),
        ]:
            yield from self._emit_block(
                block, _YEARS[:8], _SUFFIXES[:5], _SEPS[:3], score, seen, count,
            )
            if self.max_candidates and count[0] >= self.max_candidates:
                return
        for sur in _SURNAMES_PINYIN[:15]:
            for name in _NAMES_PINYIN[:10]:
                cand = f"{sur}{name}"
                if cand not in seen:
                    seen.add(cand)
                    count[0] += 1
                    if self.max_candidates and count[0] >= self.max_candidates:
                        return
                    yield (cand, 0.65)

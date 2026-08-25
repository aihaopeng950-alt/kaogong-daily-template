#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 - GitHub Actions 

  -  07:00 = ///
  -  22:00 =  +  + 
 GitHub 


  1)  /   banks.json
  2)  /  
  3)  sent_history.json 
  4)  (, ) 
"""

import os
import csv
import json
import smtplib
import datetime
import subprocess
import requests
import re
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

# -------------------------  -------------------------
CITY = "郑州"
LAT, LON = 34.7466, 113.6253          # 郑州坐标
TZ_HOURS = 8                           # 北京时间 UTC+8
HISTORY_FILE = "sent_history.json"
HISTORY_KEEP = 60                      # 历史保留记录条数（≈30天=60条/每天2次；须 > 14天防重窗口*2）
COURSE_FILE = "courses.csv"               # 课表（图片版已核对）

#  ->
BOARDS = {
    0: "政治", 1: "法律", 2: "中国历史", 3: "前沿科技",
    4: "地理国情", 5: "宏观经济", 6: "公文管理",
}
WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

# -------------------------  -------------------------
#  GPT  →  →  →
#  16 2026-08-10  11/23-11/29 2026-11-28
PLAN_START = datetime.date(2026, 8, 10)      # 第 1 周周一
EXAM_DATE = datetime.date(2026, 11, 28)       # 国考笔试日
TOOL_AUTHOR = "ahp"                            # anti-plagiarism watermark

WEEKLY_PLAN = [
    {"week": 1, "rng": "8/10–8/16", "stage": "阶段一 · 补能力缺口（8月）",
     "xcz": "数量起步：工程问题+行程问题题型体系（每天60min系统学，先建方法而非刷题）；政治理论：马原基本框架（40min）；言语10-15题保手感、重点看错因；判断统计图形/定义/类比/逻辑哪类最差；资料练速度（目标40min内）；常识碎片10min。",
     "sl": "概括归纳入门：学会材料→找点→分类→表述，每周3次×45-60min。",
     "sz": "低频接触，本周1次×20min了解大事即可。",
     "tip": "明天先花60min搭「工程问题」题型框架（公式+2道例题），再用40min过马原导论；言语/资料各做15题保持手感。别做整套卷，先把「不会」变「会」。"},
    {"week": 2, "rng": "8/17–8/23", "stage": "阶段一 · 补能力缺口（8月）",
     "xcz": "数量：经济利润+溶液浓度；政治理论：毛中特+中特体系框架；判断专项攻弱项（如定义判断）；资料继续压速度；言语维持85%、资料维持80%。",
     "sl": "概括归纳强化：能准确解释每个得分点为何存在。",
     "sz": "1-2次×20-30min。",
     "tip": "明天攻「经济利润」题型（利润/折扣/统筹），政治理论补毛中特脉络；判断专项刷定义判断并统计错因。"},
    {"week": 3, "rng": "8/24–8/30", "stage": "阶段一 · 补能力缺口（8月）",
     "xcz": "数量：排列组合+概率+容斥（只学常考方法）；政治理论：习思想+党史+重要会议；判断弱项再专项；资料速度稳至35min内。",
     "sl": "综合分析：训练「是什么→为什么→怎么办」。",
     "sz": "1-2次。",
     "tip": "明天学排列组合基础（分类分步原理），政治理论梳理党史时间轴；申论做2道综合分析题。"},
    {"week": 4, "rng": "8/31–9/6", "stage": "阶段二 · 补短板+真题化（9月）",
     "xcz": "数量：年龄/日期/周期+和差倍比；政治理论：法律基础+经济政治文化；开始「补短」——统计各模块薄弱题型；时间比：数量45/政治30/三大模块75/常识15/复盘15。",
     "sl": "对策+公文格式入门；大作文每周1篇（立意+结构优先）。",
     "sz": "适度增加，2次。",
     "tip": "明天起给题目分类（A马上做/B思考可做/C大量计算跳/D完全不会猜），数量学年龄日期周期题；申论练1道对策题。"},
    {"week": 5, "rng": "9/7–9/13", "stage": "阶段二 · 补短板+真题化（9月）",
     "xcz": "三大模块补短75min；数量45min维持；政治30min；常识15min；错题复盘15min。本周起每周至少1套完整行测（严格120min）。",
     "sl": "小题训练+大作文，逐步真题化。",
     "sz": "2次。",
     "tip": "明天做本周第1套完整行测（严格120min），重点复盘「做对但慢」「做错但会」两类题，不追题量。"},
    {"week": 6, "rng": "9/14–9/20", "stage": "阶段二 · 补短板+真题化（9月）",
     "xcz": "补短+真题化；数量必做题型巩固；判断弱项再专项（如逻辑判断）。",
     "sl": "小题+大作文，注意不跑题、回扣材料。",
     "sz": "2次。",
     "tip": "明天针对上周模考薄弱模块专项训练30min，数量做工程/利润巩固；申论写1篇大作文（结构优先）。"},
    {"week": 7, "rng": "9/21–9/27", "stage": "阶段二 · 补短板+真题化（9月）",
     "xcz": "继续补短；本周第2套真题；政治理论不再纯蒙。",
     "sl": "公文格式+大作文结构。",
     "sz": "2次。",
     "tip": "明天做第2套完整真题并统计模块得分/耗时；申论写1篇大作文，重点检查分论点与回扣材料。"},
    {"week": 8, "rng": "9/28–10/4", "stage": "阶段二收尾（9月底）",
     "xcz": "9月底目标模考稳定70-73；三大模块正确率保持；数量稳定得分；政治非纯蒙；120min覆盖更多题。",
     "sl": "整套申论1套。",
     "sz": "2次。",
     "tip": "明天做9月最后一套模考，对照「66-68危险线」检查：若仍低于70需调整策略而非加时长；申论1套。"},
    {"week": 9, "rng": "10/5–10/11", "stage": "阶段三 · 速度+整套（10月）",
     "xcz": "真题+限时+复盘：每周2套完整；剩余时间模块训练；目标120min稳定多做。",
     "sl": "真题主导，2次小题+1大作文+1整套。",
     "sz": "系统整理启动，2-3次（会议/政策/河南）。",
     "tip": "明天实验第1种做题顺序（言语→判断→资料→常识→数量）并记录得分；数量锁定必做题型（工程/利润/行程/和差倍比/容斥）。"},
    {"week": 10, "rng": "10/12–10/18", "stage": "阶段三 · 速度+整套（10月）",
     "xcz": "限时提速；实验顺序B（常识→言语→判断→资料→数量）；资料压至30-35min。",
     "sl": "真题+控时。",
     "sz": "2-3次系统整理。",
     "tip": "明天测第2种做题顺序并对比哪种实际得分高（非舒适感）；申论控时做1套小题。"},
    {"week": 11, "rng": "10/19–10/25", "stage": "阶段三 · 速度+整套（10月）",
     "xcz": "实验顺序C（资料→判断→言语→常识→数量）；数量形成「必做题库」，复杂排列组合可放弃。",
     "sl": "真题整套+大作文。",
     "sz": "3次高频整理。",
     "tip": "明天确定自己的最优做题顺序（按得分非舒适）；数量只练必做5类，复杂题果断跳。"},
    {"week": 12, "rng": "10/26–11/1", "stage": "阶段三收尾（10月底）",
     "xcz": "稳定73-76；真题限时固化顺序；错题复盘。",
     "sl": "整套+作文。",
     "sz": "3次。",
     "tip": "明天做10月最后一套模考，目标稳定73+；复盘必做题型清单与高频易错点。"},
    {"week": 13, "rng": "11/2–11/8", "stage": "阶段四 · 冲刺稳定75+（11/1–15）",
     "xcz": "每周2-3套完整模拟（严格考试环境）；每次考后统计总分+模块得分+耗时+错题类型。",
     "sl": "每周1-2套完整。",
     "sz": "高频背诵启动。",
     "tip": "明天按正式考试环境做第1套冲刺模考（含申论），重点盯「最低分」而非最高分；统计四类题。"},
    {"week": 14, "rng": "11/9–11/15", "stage": "阶段四 · 冲刺稳定75+（11/1–15）",
     "xcz": "第2-3套模考；稳定75+。",
     "sl": "整套训练。",
     "sz": "高频背诵。",
     "tip": "明天做第2套冲刺模考并对比上次稳定性（目标72/74/75/73/76型）；申论1套。"},
    {"week": 15, "rng": "11/16–11/22", "stage": "阶段五 · 查漏补缺保状态（11/16–28）",
     "xcz": "不学新内容：只过错题/高频/数量必做/政治/时政/顺序/时间分配。",
     "sl": "高频问题+公文格式+答题逻辑+作文结构+常用表达。",
     "sz": "最后强化，最后两周高频滚动。",
     "tip": "明天只复习不刷题量——过一遍数量必做题型+政治理论框架+错题本；早睡把状态调到考试节奏。"},
    {"week": 16, "rng": "11/23–11/29", "stage": "阶段五 · 考试周（11/29考试）",
     "xcz": "保持手感、轻量；错题+高频；严格稳定睡眠。",
     "sl": "保持手感，作文结构默写。",
     "sz": "最后强化。",
     "tip": "明天做一套轻量保温卷（不追强度），重点看错题本和公式卡；11/28国考，作息调至考试节奏，不学新东西。"},
]

def week_for(target_date):
    """ target_date /"""
    idx = (target_date - PLAN_START).days // 7
    idx = max(0, min(idx, len(WEEKLY_PLAN) - 1))
    return WEEKLY_PLAN[idx]


def days_to_exam(d: datetime.date) -> int:
    """EXAM_DATEd  0"""
    return (EXAM_DATE - d).days


# WMO  ->
WMO = {
    0: "晴", 1: "晴间多云", 2: "多云", 3: "阴",
    45: "雾", 48: "雾凇",
    51: "毛毛雨", 53: "毛毛雨", 55: "毛毛雨",
    56: "冻毛毛雨", 57: "冻毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    66: "冻雨", 67: "冻雨",
    71: "小雪", 73: "中雪", 75: "大雪", 77: "雪粒",
    80: "阵雨", 81: "阵雨", 82: "强阵雨",
    85: "阵雪", 86: "强阵雪",
    95: "雷阵雨", 96: "雷阵雨伴冰雹", 99: "雷阵雨伴冰雹",
}
COMPASS = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]


def beaufort(kmh: float) -> int:
    """km/h """
    thresholds = [1, 5, 11, 19, 28, 38, 49, 61, 74, 88, 102, 117]
    for i, t in enumerate(thresholds):
        if kmh <= t:
            return i
    return 12


def wind_dir(deg: float) -> str:
    return COMPASS[round(deg / 45) % 8]


# -------------------------  -------------------------
def load_banks():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banks.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("题库读取失败（将用兜底）：", e)
        return {"quotes": [], "idioms": []}


BANKS = load_banks()


def pick_quotes(day: int, n: int = 2):
    qs = BANKS.get("quotes", [])
    if not qs:
        return ["（题库缺失）", "（题库缺失）"]
    #  day*2  2
    base = (day * 2) % len(qs)
    return [qs[(base + i) % len(qs)] for i in range(n)]


def pick_idioms(day: int, n: int = 3):
    its = BANKS.get("idioms", [])
    if not its:
        return [{"a": "A", "b": "B", "diff": "题库缺失", "example": ""} for _ in range(n)]
    #  3
    return [its[(day + off) % len(its)] for off in (0, 13, 27)][:n]


def pick_knowledge(board: str, day: int, n: int = 1):
    """"""
    items = BANKS.get("knowledge", {}).get(board, [])
    if not items:
        return [{"title": "（考点缺失）", "content": f"请检查 banks.json 的 knowledge.{board} 板块。"}]
    base = day % len(items)
    return [dict(items[(base + i) % len(items)]) for i in range(n)]


# -------------------------  -------------------------
#  PLAN_START2026-08-10 1  ( - PLAN_START).days % 5
WUHAO_ORDER = ["经济", "政治", "文化", "社会", "生态"]


def dimension_for(d: datetime.date) -> str:
    """ d """
    idx = (d - PLAN_START).days % 5
    return WUHAO_ORDER[idx]


def _extract_json(text: str) -> dict:
    """ LLM  JSON ```json """
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n?", "", s)
        s = re.sub(r"\n?```$", "", s).strip()
    try:
        return json.loads(s)
    except Exception:
        pass
    i = s.find("{"); j = s.rfind("}")
    if i >= 0 and j > i:
        return json.loads(s[i:j + 1])
    raise ValueError("无法解析 LLM 返回的 JSON")


def gen_wuhao_block(dim: str, quote: str, source: str) -> dict:
    """· LLM   /  / 250+
     dict{interpretation, sub_point, material} wuhao_fallback[dim]
    """
    fb = (BANKS.get("wuhao_fallback", {}) or {}).get(dim) or {}
    try:
        api_key = os.environ.get("LLM_API_KEY")
        if not api_key:
            return dict(fb)
        base = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")
        model = os.environ.get("LLM_MODEL") or "deepseek-v4-flash"  # 与 gen_content 统一读取 LLM_MODEL
        prompt = (
            f"你是考公申论素材生成助手。给定一句名言及其出处，请为申论大作文「{dim}」维度的论证生成素材。\n"
            f"名言：{quote}\n出处：{source}\n\n"
            "请严格以 JSON 格式返回，包含三个字段：\n"
            "1) interpretation：释义，用一句话（约40-60字）解释这句名言的涵义，并点明它与「" + dim + "」维度的关联；\n"
            "2) sub_point：分论点，用一句话（约40-60字）提炼可用于该维度大作文的分论点；\n"
            "3) material：具体论证，约250字，须同时包含道理论证与举例论证（举一个真实可考的政策案例或典型事实），语言符合申论规范。\n"
            "只返回 JSON，不要任何额外说明，不要用代码块包裹。"
        )
        resp = requests.post(
            base + "/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7},
            timeout=60,
        )
        resp.raise_for_status()
        data = _extract_json(resp.json()["choices"][0]["message"]["content"])
        interp = (data.get("interpretation") or "").strip()
        sub = (data.get("sub_point") or "").strip()
        mat = (data.get("material") or "").strip()
        if not (interp and sub and mat):
            raise ValueError("LLM 返回字段不完整")
        return {"interpretation": interp, "sub_point": sub, "material": mat}
    except Exception as e:
        print(f"五位一体申论素材 LLM 生成失败，回退静态兜底：{e}")
        return dict(fb)


def pick_wuhao(d: datetime.date) -> dict:
    """ d  +  +  +  + 

     12/31 
     /  /  LLM  wuhao_fallback 
    """
    dim = dimension_for(d)
    pool = BANKS.get("wuhao_yiti", {}).get(dim, [])
    if not pool:
        return {"dimension": dim, "quote": "（素材缺失）", "quote_source": "",
                "interpretation": "", "sub_point": "",
                "material": f"请检查 banks.json 的 wuhao_yiti.{dim} 板块。"}
    k = (d - PLAN_START).days // 5
    entry = dict(pool[k % len(pool)])   # 名言（含出处）静态取，保准确与维度精准
    entry["dimension"] = dim
    blk = gen_wuhao_block(dim, entry.get("quote", ""), entry.get("quote_source", ""))
    entry["interpretation"] = blk.get("interpretation", "")
    entry["sub_point"] = blk.get("sub_point", "")
    entry["material"] = blk.get("material", "")
    return entry


# -------------------------  -------------------------
def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"records": []}


def save_history(hist):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(hist, f, ensure_ascii=False, indent=2)


def git_commit_history(date_str: str):
    """"""
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("未检测到 GH_TOKEN，跳过历史提交（不影响邮件）。")
        return
    try:
        repo = os.environ.get("GITHUB_REPOSITORY", "aihaopeng950-alt/kaogong-daily")
        url = f"https://x-access-token:{token}@github.com/{repo}.git"
        subprocess.run(["git", "config", "user.email", "bot@workbuddy.local"], check=True)
        subprocess.run(["git", "config", "user.name", "WorkBuddy Bot"], check=True)
        subprocess.run(["git", "add", HISTORY_FILE], check=True)
        subprocess.run(["git", "commit", "-m", f"chore: update sent history {date_str}"], check=True)
        subprocess.run(["git", "push", url, "HEAD:main"], check=True)
        print("已提交历史记录到仓库。")
    except Exception as e:
        print("历史提交失败（不影响已发送邮件）：", e)


# ------------------------- 1.  -------------------------
def get_weather(day_offset: int = 0):
    """day_offset=0 =1 """
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        "&current=temperature_2m,weather_code,wind_speed_10m,wind_direction_10m"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min,wind_speed_10m_max"
        f"&timezone=Asia%2FShanghai&forecast_days=2"
    )
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    d = r.json()
    daily = d["daily"]
    code = int(daily["weather_code"][day_offset])
    wspd = float(daily["wind_speed_10m_max"][day_offset])
    lv = beaufort(wspd)
    if day_offset == 0:
        wdir = wind_dir(float(d["current"]["wind_direction_10m"]))
        wind = f"{wdir}风 {lv}级（{wspd:.0f} km/h）"
    else:
        wind = f"风力 {lv}级（{wspd:.0f} km/h）"
    return {
        "desc": WMO.get(code, "未知"),
        "tmin": daily["temperature_2m_min"][day_offset],
        "tmax": daily["temperature_2m_max"][day_offset],
        "wind": wind,
    }


# ------------------------- 2.  +  +  -------------------------
def parse_cn_date(s):
    """ '20260825'  datetime.date None"""
    m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", s or "")
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except Exception:
        return None


def gen_content(board: str, weekday_str: str, day_hint: int, history: dict) -> dict:
    api_key = os.environ.get("LLM_API_KEY", "")
    # API  base + "/chat/completions"
    # DeepSeek  https://api.deepseek.com /v1
    base = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")
    #  LLM_MODEL daily.yml  deepseek-v4-flash
    model = os.environ.get("LLM_MODEL") or "deepseek-v4-flash"
    src = "LLM_MODEL(配置值)" if os.environ.get("LLM_MODEL") else "默认 deepseek-v4-flash"
    print("使用模型:", model, f"({src})", "| 接口:", base + "/chat/completions")

    schema = '''{
  "board": "板块名",
  "knowledge": {"title": "考点名", "content": "2-3句话精简考点，好记忆"},
  "politics": [
    {"title": "时政热点①标题", "content": "一句话热点概述 + 为何可考/对应考点（2-3句）"},
    {"title": "时政热点②标题", "content": "一句话热点概述 + 为何可考/对应考点（2-3句）"}
  ],
  "tip": "一句简短穿衣/出行提示"
}'''
    # "" 14
    #  [-14:]  records 14 ≈7
    _now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=TZ_HOURS))).date()
    _cutoff = _now - datetime.timedelta(days=14)
    recent = [r for r in history.get("records", [])
              if (d := parse_cn_date(r.get("date", ""))) and d >= _cutoff]
    avoid = ""
    used_k = "\n".join(f"  - {r.get('knowledge','')}" for r in recent if r.get("knowledge"))
    used_p = "\n".join(f"  - {t}" for r in recent for t in r.get("politics", []) if t)
    if used_k.strip():
        avoid += (f"\n【防重复·常识考点】以下考点最近 14 天已推送过，今天务必不要重复，"
                   f"请另选一个新的、具体的「{board}」高频考点：\n{used_k}\n")
    if used_p.strip():
        avoid += (f"【防重复·时事政治】以下时政标题最近 14 天已推送过，今天务必不要重复：\n{used_p}\n")

    prompt = (
        f"你是考公备考内容生成助手。今天是{weekday_str}，常识板块为「{board}」。\n"
        "请严格遵守以下 JSON 格式输出（只输出 JSON，不要有任何多余文字、不要加 ``` 包裹）：\n"
        f"{schema}\n"
        f"要求：常识考点紧扣「{board}」板块且高频易考、简短好记，必须是全新的具体考点；"
        "tip 结合当天天气给出。"
        "时事政治：从近期（近一年）重大时政与政治要闻中，挑选最有可能在公考中出现的热点，优先选取与历年真题、高频考点契合度高的主题（如党和国家重要会议精神、重大政策方针、发展战略、重要成就、法治与民生、国际关系等）。"
        f"生成2条考公高频时政考点，两条主题不同、互不重复，并点明其与考点的关联与可考原因；今天是年内第 {day_hint} 天，请确保这两条时政内容与其他日期尽量不同，贴近考情、突出可考性。"
        + avoid
    )

    resp = requests.post(
        base + "/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7},
        timeout=60,
    )
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"]
    return _extract_json(text)


def default_content(board: str, day_hint: int = 0):
    """LLM 
     day_hint  LLM """
    kb = BANKS.get("knowledge", {}).get(board, [])
    know = kb[0] if kb else {"title": "（生成失败，使用默认占位）",
                             "content": "今日内容生成异常，请检查 LLM_API_KEY 配置或手动补卡。"}
    pol_list = BANKS.get("politics", [])
    if pol_list:
        n = len(pol_list)
        start = day_hint % n
        picked = [pol_list[(start + i) % n] for i in range(min(2, n))]
        pols = [{"title": p.get("title", ""), "content": p.get("content", "")} for p in picked]
    else:
        pols = [
            {"title": "（时政①生成失败）", "content": "请检查 LLM_API_KEY 配置或手动补时政。"},
            {"title": "（时政②生成失败）", "content": "请检查 LLM_API_KEY 配置或手动补时政。"},
        ]
    return {
        "board": board,
        "knowledge": know,
        "quotes": pick_quotes(0, 2),
        "idioms": pick_idioms(0, 3),
        "politics": pols,
        "tip": "天气数据见上，注意合理安排出行。",
    }


# -------------------------  CSV -------------------------
def load_course(day_offset: int = 0):
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=TZ_HOURS)))
    target = (now + datetime.timedelta(days=day_offset)).date().isoformat()
    try:
        with open(COURSE_FILE, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("date") == target:
                    return row
    except Exception as e:
        print("课表读取失败：", e)
    return None


def course_html(course_row, title="今日课程表"):
    """HTML title /"""
    if not course_row:
        inner = "暂无课表安排，好好休息 / 自主复习"
        border, color = "#94a3b8", "#64748b"
    else:
        c = course_row
        parts = ["课程：" + str(c.get("course", "")) + "（" + str(c.get("phase", "")) + "阶段）"]
        if c.get("tags"):
            parts.append("科目：" + str(c["tags"]))
        if c.get("detail"):
            parts.append("安排：" + str(c["detail"]))
        inner = "<br>".join(parts)
        border, color = "#0ea5e9", "#0284c7"
    return (
        '<div style="background:#fff;border-radius:12px;padding:16px 20px;'
        "margin-bottom:16px;border-left:4px solid " + border + ";"
        'box-shadow:0 2px 8px rgba(0,0,0,0.04);">'
        '<h2 style="color:' + color + ';font-size:16px;margin:0 0 10px 0;">' + title + '</h2>'
        '<p style="font-size:14px;color:#374151;line-height:1.8;margin:0;">' + inner + "</p>"
        "</div>"
    )


# ------------------------- 3.  HTML -------------------------
def build_html(date_str, weekday_str, content, exam_days=None):
    k = content["knowledge"]
    pol_list = content.get("politics", [])
    idioms = content.get("idioms", [])
    board = content.get("board", "")

    wuhao = content.get("wuhao") or {}
    if wuhao:
        wuhao_html = (
            '<div style="background: #ecfdf5; border-radius: 8px; padding: 12px 16px; margin-bottom: 14px;">\n'
            '<p style="font-size: 14px; margin: 0 0 8px 0;">'
            '<span style="background: #10b981; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 12px;">申论素材 · 五位一体</span> '
            f'<span style="color: #6b7280; font-size: 11px;">今日维度：{wuhao.get("dimension","")}</span></p>\n'
            '<p style="font-size: 14px; color: #1f2937; line-height: 1.8; margin: 0;">\n'
            f'<strong>📜 名言：</strong>{wuhao.get("quote","")}（{wuhao.get("quote_source","")}）<br>\n'
            f'<strong>📖 释义：</strong>{wuhao.get("interpretation","")}<br>\n'
            f'<strong>🎯 分论点：</strong>{wuhao.get("sub_point","")}<br>\n'
            f'<strong>📝 具体论证：</strong>{wuhao.get("material","")}\n'
            '</p>\n</div>\n'
        )
    else:
        wuhao_html = ""

    politics_html = ""
    for i, p in enumerate(pol_list[:2], 1):
        politics_html += (
            f'<div style="background: #fef2f2; border-radius: 8px; padding: 12px 16px; margin-bottom: 14px;">\n'
            f'<p style="font-size: 14px; margin: 0 0 6px 0;"><span style="background: #dc2626; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 12px;">时事政治 {i}</span> <span style="color: #6b7280; font-size: 11px;">每日热点</span></p>\n'
            f'<p style="font-size: 14px; color: #1f2937; line-height: 1.8; margin: 0;">\n'
            f'<strong>{p.get("title", "")}</strong><br>\n'
            f'{p.get("content", "")}\n'
            f'</p>\n</div>\n'
        )

    idiom_html = ""
    for i, it in enumerate(idioms[:3], 1):
        idiom_html += (
            f'{i}️⃣ <strong>{it["a"]} VS {it["b"]}</strong>：{it["diff"]}。'
            f'例句：{it["example"]}<br>\n'
        )

    if exam_days is not None:
        banner = (
            '<div style="background: linear-gradient(90deg, #b91c1c, #ef4444); border-radius: 12px; '
            'padding: 18px 20px; margin-bottom: 16px; text-align: center;">\n'
            '<p style="color: #ffffff; font-size: 14px; margin: 0 0 4px 0; opacity: 0.9;">距离国考还剩多少天</p>\n'
            f'<p style="color: #ffffff; font-size: 34px; font-weight: bold; margin: 0; letter-spacing: 1px;">{exam_days} 天</p>\n'
            '<p style="color: rgba(255,255,255,0.85); font-size: 12px; margin: 4px 0 0 0;">2026年11月28日 · 国考笔试</p>\n'
            '</div>\n'
        )
    else:
        banner = ""

    return f"""<div style="font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif; max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #f0f9ff 0%, #fef3c7 50%, #f0fdf4 100%); border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">

<div style="background: linear-gradient(90deg, #1e40af, #3b82f6); padding: 20px 24px; text-align: center;">
<h1 style="color: #fff; font-size: 20px; margin: 0; letter-spacing: 2px;">📮 考公每日加油站</h1>
<p style="color: rgba(255,255,255,0.8); font-size: 12px; margin: 6px 0 0 0;">{date_str} {weekday_str} · 每天进步一点点 ✨</p>
</div>

<div style="padding: 20px 24px;">

{banner}
<div style="background: #fff; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
<h2 style="color: #7c3aed; font-size: 16px; margin: 0 0 16px 0; border-bottom: 2px dashed #e9d5ff; padding-bottom: 8px;">📖 每日公考打卡素材</h2>

<div style="background: #faf5ff; border-radius: 8px; padding: 12px 16px; margin-bottom: 14px;">
<p style="font-size: 14px; margin: 0 0 6px 0;"><span style="background: #7c3aed; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 12px;">常识考点</span> <span style="color: #6b7280; font-size: 11px;">板块：{board}</span></p>
<p style="font-size: 14px; color: #1f2937; line-height: 1.8; margin: 0;">
<strong>{k['title']}</strong><br>
{k['content']}
</p>
</div>

{politics_html}
{wuhao_html}

<div style="background: #fff7ed; border-radius: 8px; padding: 12px 16px;">
<p style="font-size: 14px; margin: 0 0 10px 0;"><span style="background: #f97316; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 12px;">易混成语 3组</span></p>
<p style="font-size: 13px; color: #374151; line-height: 2; margin: 0;">
{idiom_html}</p>
</div>
</div>

<div style="text-align: center; padding-top: 12px; border-top: 1px solid #e5e7eb;">
<p style="color: #9ca3af; font-size: 11px; margin: 0;">
🕖 每天早上 7:00 自动推送 · 坚持就是胜利 🎯<span style="display:none">ahp</span>
</p>
</div>

</div>
</div>"""


# ------------------------- 3b.  -------------------------
def gen_tip(w: dict) -> str:
    """/ LLM """
    desc = w.get("desc", "")
    try:
        tmax = float(w.get("tmax", "nan"))
    except (ValueError, TypeError):
        tmax = None
    if "雨" in desc or "雪" in desc:
        return "明日有降水，记得带伞🌂，穿防滑鞋。"
    if tmax is not None and tmax >= 33:
        return "明日晴热，注意防晒补水🧴，备好饮用水。"
    if tmax is not None and tmax <= 5:
        return "明日寒冷，注意保暖🧣，尤其早晚温差大。"
    return "明日天气平稳，合理安排作息，学习更高效。"


def build_evening_html(date_str, weekday_str, weather, course_row):
    """ +  +  + ()"""
    try:
        d = datetime.datetime.strptime(date_str, "%Y年%m月%d日").date()
    except Exception:
        d = datetime.date.today()
    wk = week_for(d)
    if course_row:
        course_block = course_html(dict(course_row), title="📚 培训班明日课表")
    else:
        course_block = course_html(None, title="📚 培训班明日课表")
    tip = gen_tip(weather)
    plan_card = f"""<div style="background: #fff; border-radius: 12px; padding: 16px 20px; margin-bottom: 16px; border-left: 4px solid #6366f1; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
<h2 style="color: #4f46e5; font-size: 16px; margin: 0 0 4px 0;">📋 本周备考计划（第{wk['week']}周 · {wk['rng']}）</h2>
<p style="font-size: 13px; color: #6b7280; margin: 0 0 12px 0;">{wk['stage']}</p>
<div style="margin-bottom: 10px;"><span style="background:#6366f1;color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;">行测</span><p style="font-size:14px;color:#374151;line-height:1.8;margin:6px 0 0 0;">{wk['xcz']}</p></div>
<div style="margin-bottom: 10px;"><span style="background:#0ea5e9;color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;">申论</span><p style="font-size:14px;color:#374151;line-height:1.8;margin:6px 0 0 0;">{wk['sl']}</p></div>
<div><span style="background:#f59e0b;color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;">时政</span><p style="font-size:14px;color:#374151;line-height:1.8;margin:6px 0 0 0;">{wk['sz']}</p></div>
</div>"""
    return f"""<div style="font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif; max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #f0f9ff 0%, #fef3c7 50%, #f0fdf4 100%); border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">

<div style="background: linear-gradient(90deg, #0ea5e9, #22d3ee); padding: 20px 24px; text-align: center;">
<h1 style="color: #fff; font-size: 20px; margin: 0; letter-spacing: 2px;">📅 明日课程预告</h1>
<p style="color: rgba(255,255,255,0.85); font-size: 12px; margin: 6px 0 0 0;">{date_str} {weekday_str} · 第{wk['week']}周 · {wk['stage']}</p>
</div>

<div style="padding: 20px 24px;">

<div style="background: #fff; border-radius: 12px; padding: 16px 20px; margin-bottom: 16px; border-left: 4px solid #f59e0b; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
<h2 style="color: #d97706; font-size: 16px; margin: 0 0 10px 0;">🌤️ 明日{CITY}天气</h2>
<p style="font-size: 14px; color: #374151; line-height: 1.8; margin: 0;">
📅 {date_str} {weekday_str}<br>
☁️ 天气：{weather['desc']}<br>
🌡️ 气温：{weather['tmin']}℃ ~ {weather['tmax']}℃<br>
💨 风力：{weather['wind']}<br>
💡 出行提示：{tip}
</p>
</div>

{course_block}
<div style="background: #fff; border-radius: 12px; padding: 16px 20px; margin-bottom: 16px; border-left: 4px solid #10b981; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
<h2 style="color: #059669; font-size: 16px; margin: 0 0 10px 0;">💡 明天建议怎么干（第{wk['week']}周）</h2>
<p style="font-size: 14px; color: #374151; line-height: 1.8; margin: 0;">
{wk['tip']}
</p>
</div>

{plan_card}

<div style="text-align: center; padding-top: 12px; border-top: 1px solid #e5e7eb;">
<p style="color: #9ca3af; font-size: 11px; margin: 0;">
🕖 每晚 22:00 自动预告 · 坚持就是胜利 🎯<span style="display:none">ahp</span>
</p>
</div>

</div>
</div>"""


# ------------------------- 4. 163 SMTP -------------------------
def send_email(html: str, subject: str, sender_name: str = "公考每日推送"):
    user = os.environ["EMAIL_USER"]
    pwd = os.environ["EMAIL_AUTH_CODE"]
    # EMAIL_TO a@qq.com,b@qq.com
    raw = os.environ.get("EMAIL_TO", "2089178729@qq.com")
    recipients = [x.strip() for x in raw.split(",") if x.strip()]
    if not recipients:
        recipients = ["2089178729@qq.com"]

    msg = MIMEText(html, "html", "utf-8")
    # ==
    msg["From"] = formataddr((sender_name, user), "utf-8")
    msg["To"] = Header(", ".join(recipients))
    msg["Subject"] = Header(subject, "utf-8")

    with smtplib.SMTP_SSL("smtp.163.com", 465, timeout=20) as s:
        s.login(user, pwd)
        s.sendmail(user, recipients, msg.as_string())
    print("已发送给", len(recipients), "位收件人：", ", ".join(recipients))


# -------------------------  -------------------------
def main():
    mode = (os.environ.get("PUSH_MODE") or "").strip().lower()
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=TZ_HOURS)))
    # 12 ==
    if not mode:
        mode = "morning" if now.hour < 12 else "evening"

    offset = 0 if mode == "morning" else 1            # 早上看今天，晚上看明天
    target = now + datetime.timedelta(days=offset)
    weekday = target.weekday()
    board = BOARDS[weekday]
    date_str = target.strftime("%Y年%m月%d日")         # 邮件里显示的日期（目标日）
    weekday_str = WEEKDAYS[weekday]
    day_hint = target.timetuple().tm_yday              # 年内第几天，用于题库轮换

    send_date = now.strftime("%Y年%m月%d日")            # 去重用的实际发送日
    history = load_history()

    if any(r.get("date") == send_date and r.get("mode") == mode
           for r in history.get("records", [])):
        print(f"【{mode}】{send_date} 已发送过，跳过以避免重复邮件。")
        return

    try:
        weather = get_weather(offset)
    except Exception as e:
        print("天气获取失败，使用占位：", e)
        weather = {"desc": "（天气获取失败）", "tmin": "-", "tmax": "-", "wind": "-"}

    if mode == "morning":
        try:
            content = gen_content(board, weekday_str, day_hint, history)
        except Exception as e:
            print("内容生成失败，使用默认占位：", e)
            content = default_content(board, day_hint)
        #  LLM
        content["knowledge"] = pick_knowledge(board, day_hint, 1)[0]
        content["wuhao"] = pick_wuhao(target.date())
        content["idioms"] = pick_idioms(day_hint, 3)
        exam_days = days_to_exam(now.date())
        html = build_html(date_str, weekday_str, content, exam_days)
        subject = f"【考公每日加油站】{date_str} · 距离国考还剩{exam_days}天"
        sender_name = "公考每日推送"
    else:
        course_row = load_course(1)
        html = build_evening_html(date_str, weekday_str, weather, course_row)
        subject = f"【明日课程预告】{date_str} · {CITY}天气 + 明日课表"
        sender_name = "明日课程预告"

    send_email(html, subject, sender_name)
    print("已发送：", subject)

    history.setdefault("records", [])
    rec = {"date": send_date, "mode": mode}
    if mode == "morning":
        rec.update({
            "board": board,
            "knowledge": content["knowledge"].get("title", ""),
            "politics": [p.get("title", "") for p in content.get("politics", [])],
        })
    else:
        rec["course"] = course_row.get("course", "") if course_row else ""
    history["records"].append(rec)
    history["records"] = history["records"][-HISTORY_KEEP:]
    save_history(history)
    git_commit_history(send_date)


if __name__ == "__main__":
    main()

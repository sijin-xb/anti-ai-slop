from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

try:
    from .rules import SEVERITY_BY_ID, SEVERITY_RANK
except ImportError:
    from rules import SEVERITY_BY_ID, SEVERITY_RANK

TEXT_SUFFIXES = {".md", ".markdown", ".mdx", ".txt", ".rst"}
FENCE_SUFFIXES = TEXT_SUFFIXES - {".rst"}

Pattern = tuple[str, re.Pattern[str], str]

HINTS = {
    "thinking-leak": "疑似暴露处理过程；正文应直接呈现发现或结果",
    "meta": "疑似文档元话语或 AI 自指；直接进入技术内容",
    "filler": "疑似空泛套话或无依据营销词；换成具体技术事实或边界",
    "overclaim": "绝对化表述需要证据或适用边界",
    "closer": "收尾客套；删除无实际作用的部分",
}

def build_pack(**sources: str) -> tuple[Pattern, ...]:
    pack = []
    for key, source in sources.items():
        category = key.replace("_", "-")
        pack.append((category, re.compile(source, re.IGNORECASE | re.MULTILINE), HINTS[category]))
    return tuple(pack)

UNIVERSAL_PACK = build_pack(
    meta=r"\bAs an AI(?: language model)?\b|\bas a large language model\b",
    overclaim=r"(?<!\d)100\s?%",
)

ZH_PACK = build_pack(
    thinking_leak=(
        r"我(?:需要|们要)先(?:看|检查|分析|梳理|确认|整理)|"
        r"让我(?:先|来|再)?(?:看|检查|分析|梳理|确认|整理)|"
        r"接下来我(?:会|将|要)(?:先)?(?:看|检查|分析|梳理|确认|整理)|"
        r"(?<![：:\s当若如])用户(?:想要|希望|要求)的是"
    ),
    meta=(
        r"(?:本文档|本文件)(?:旨在|主要用于|将会)|"
        r"下面(?:将)?(?:分为|从.{0,12}方面)(?:介绍|说明)|"
        r"接下来(?:将)?(?:介绍|说明)|"
        r"本文将带(?:你|您)|"
        r"作为(?:一个)?(?:AI|人工智能)(?:助手|模型)?"
    ),
    filler=(
        r"值得注意的是|需要注意的是|需要指出的是|总的来说|综上所述|总而言之|"
        r"(?<!非)显而易见|不难(?:看出|发现)|至关重要|不可否认(?:的是)?|毋庸置疑|深入(?:探讨|剖析)|"
        r"正如.{0,12}所说|更重要的是|不仅如此|焕发出新的活力|"
        r"在当今.{0,16}时代|随着.{0,16}发展|众所周知|"
        r"让我们(?:一起来)?(?:看看|深入)"
    ),
    overclaim=r"百分之百(?:保证|可靠|安全|准确)?|绝对不会|完全(?:杜绝|消除|避免)|零风险|毫无疑问",
    closer=(
        r"希望(?:这|本|这份)?.{0,10}(?:有帮助|帮到你)|"
        r"如有(?:任何)?(?:疑问|问题).{0,8}(?:欢迎|随时)|感谢阅读|"
        r"相信(?:你|您)已经(?:对|掌握|了解)"
    ),
)

EN_PACK = build_pack(
    thinking_leak=r"We need to (?:first )?(?:inspect|analyze|check)|Let me (?:first )?(?:inspect|analyze|check)",
    meta=r"This document (?:aims to|is intended to)|In this (?:section|document), we|^in conclusion\b|^to summarize\b",
    filler=(
        r"it is worth noting that|it is important to note that|"
        r"in today's (?:fast-paced )?(?:digital )?(?:world|landscape|era)|"
        r"in today's rapidly|as technology continues to evolve|"
        r"needless to say|at its core|to summarize,|"
        r"you will find that|to put it simply|"
        r"\bdelve into\b|\btestament to\b|\bbeacon of\b|\btapestry of\b|"
        r"\brevolutionize\b|\bcutting-edge\b|\bseamless(?:ly)?\b|"
        r"\brobust\b(?!\s+(?:error|bound|statistic|estimator|regression|outlier|tolerance))"
    ),
    overclaim=r"guaranteed to (?:always|never)|zero[- ]risk",
    closer=r"hope this helps|let me know if",
)

JA_PACK = build_pack(
    meta=(
        r"(?:AI|人工知能)(?:言語モデル|アシスタント)として|言語モデルとして|AIとして(?:、|は)|"
        r"(?:本|この)(?:記事|ドキュメント|文書|稿)(?:では|は).{0,30}(?:解説|紹介|説明)(?:します|していきます|いたします)|"
        r"以下では.{0,24}(?:解説|紹介)(?:します|していきます|いたします)|"
        r"^(?:結論として|まとめると|要約すると|総じて)"
    ),
    filler=(
        r"言うまでもなく|ご存知の通り|ご存じの通り|ご存じのとおり|周知の通り|"
        r"現代社会において|急速に進化する(?:現代|デジタル)|"
        r"注目すべき(?:点|は)|特筆すべき(?:点|は)|"
        r"深く掘り下げ|深掘りして(?:いき|みま)|"
        r"革新的な|画期的な|最先端の|シームレスな|シームレスに"
    ),
    overclaim=(
        r"完全に(?:防(?:ぐ|げ)|排除|解消|なくす)|絶対に(?:安全|失敗しません)|"
        r"ゼロリスク|間違いなく|(?:100|百)パーセント|(?:必ず|確実に)(?:成功|解決)"
    ),
    closer=(
        r"いかがでしたか|いかがでしたでしょうか|"
        r"お役に立てれば幸いです|お役に立てましたら幸いです|参考になれば幸いです|"
        r"ご不明な点がございましたら.{0,12}(?:お気軽に|お問い合わせ|ご連絡)|"
        r"最後までお読みいただき|ご覧いただきありがとうございました"
    ),
)

KO_PACK = build_pack(
    meta=(
        r"AI ?언어 ?모델(?:로서|입니다|이기)|언어 모델로서|인공지능(?:으로서|이기 때문에)|"
        r"(?:이|본) (?:문서|글)(?:은|에서는).{0,24}(?:목적으로|다룹니다|설명합니다|소개합니다)|"
        r"(?:알아보|살펴보)도록 하겠습니다|"
        r"^(?:결론적으로|요약하자면|정리하자면|종합하면)"
    ),
    filler=(
        r"말할 필요도 없이|말할 것도 없이|오늘날의 빠르게 변화하는|급변하는 .{0,12}(?:시대|환경|세상)|"
        r"(?:오늘날|현대) 사회에서|주목할 만한 (?:점은|것은)|"
        r"심층적으로 (?:살펴|분석|탐구)|"
        r"원활(?:한|하게) (?:통합|연동|연결)|혁신적인|획기적인|최첨단|"
        r"것이 (?:매우|무엇보다) 중요합니다"
    ),
    overclaim=r"절대(?:로)? (?:안전|실패하지|오류(?:가)? 없)|완벽(?:하게|히) (?:방지|해결|차단|보장)|무위험|틀림없이|100퍼센트|백 ?퍼센트",
    closer=r"도움이 되(?:셨|었)(?:기를|길|으면|다면)|궁금하신? (?:점|사항)이 있으(?:시면|면)|읽어 ?주셔서 감사합니다",
)

DE_PACK = build_pack(
    meta=(
        r"\bAls (?:KI|AI)(?:-(?:Sprachmodell|Assistent|Modell))?\b|\bAls (?:großes )?Sprachmodell\b|\bAls künstliche Intelligenz\b|"
        r"Dieses Dokument (?:soll|dient dazu|hat das Ziel|zielt darauf ab)|"
        r"In diesem (?:Abschnitt|Dokument|Artikel|Beitrag) (?:werden wir|wollen wir|möchte ich|erfahren Sie)|"
        r"^(?:Zusammenfassend(?: lässt sich sagen)?|Abschließend)\b"
    ),
    filler=(
        r"Es ist (?:wichtig|entscheidend|essenziell|essentiell) (?:zu )?(?:beachten|erwähnen|betonen|bedenken),? dass|"
        r"Es ist (?:erwähnenswert|bemerkenswert|anzumerken),? dass|"
        r"Es sei (?:darauf hingewiesen|angemerkt|erwähnt),? dass|"
        r"Es versteht sich von selbst|Unnötig zu erwähnen|Wie wir alle wissen|"
        r"In der heutigen (?:schnelllebigen |digitalen |modernen )?(?:Welt|Zeit|Ära)|Im digitalen Zeitalter|"
        r"(?:tief )?eintauchen in|taucht? (?:tief )?ein in|"
        r"\bnahtlos\w*|\brevolutionier\w*|"
        r"\bein Zeugnis (?:für|von)|\bein Beweis für|\bhochmodern\w*|Spitzentechnologie"
    ),
    overclaim=(
        r"garantiert (?:immer|nie|stets|fehlerfrei)|absolut (?:sicher|fehlerfrei|zuverlässig)|"
        r"risikofrei|ohne (?:jedes|jegliches) Risiko|hundertprozentig\w*"
    ),
    closer=(
        r"Ich hoffe,? (?:das|dies|es|diese (?:Antwort|Anleitung)) (?:hilft|war hilfreich|hat geholfen)|"
        r"Hoffentlich hilft (?:dir|euch|Ihnen) (?:das|dies)|"
        r"Zögern Sie nicht,? (?:uns |mich )?(?:zu )?(?:kontaktieren|fragen|melden)|"
        r"Bei Fragen stehe(?:n)? (?:ich|wir) (?:Ihnen |dir )?(?:gerne|jederzeit)|"
        r"Lassen Sie (?:es )?mich wissen|(?:Vielen )?Dank fürs Lesen|Danke für(?:s| das) Lesen"
    ),
)

FR_PACK = build_pack(
    meta=(
        r"En tant que (?:modèle de langage|modèle linguistique|IA|intelligence artificielle|assistante? (?:IA|virtuel(?:le)?))|"
        r"Ce document (?:vise à|a pour (?:but|objectif|vocation))|"
        r"Dans (?:cette|ce) (?:section|article|document|guide),? nous (?:allons|verrons|aborderons|explorerons)|"
        r"^(?:En conclusion|En résumé|Pour conclure|Pour résumer)\b"
    ),
    filler=(
        r"Il est (?:important|essentiel|crucial|primordial|utile) de (?:noter|souligner|rappeler|préciser|mentionner) que|"
        r"Il convient de (?:noter|souligner|préciser|mentionner) que|Il est à noter que|Il va sans dire que|"
        r"Inutile de préciser|"
        r"Dans le monde (?:d['’]aujourd['’]hui|actuel|numérique|moderne)|"
        r"À l['’]ère (?:du numérique|numérique|de l['’]information)|"
        r"Dans le paysage (?:numérique |technologique )?(?:actuel|en constante évolution)|en constante évolution|"
        r"(?:plongeons|plonger|plongez) (?:au cœur|en profondeur|dans les profondeurs)|"
        r"\brévolutionn(?:er|e|ent|aire|aires)\b|à la pointe (?:de|du)|sans couture|"
        r"un véritable témoignage|un témoignage de (?:la|l['’])"
    ),
    overclaim=(
        r"garanti sans (?:risque|erreur|faille|bug)|zéro risque|risque zéro|sans aucun risque|"
        r"absolument (?:sûr|fiable|infaillible)|infaillible"
    ),
    closer=(
        r"J['’]espère que (?:cela|ça|ce (?:guide|texte|document|message)) (?:vous )?(?:a été|sera|aide|a aidé|est)|"
        r"N['’]hésitez pas à (?:me |nous )?(?:contacter|poser|demander|solliciter|revenir)|"
        r"Je reste à votre disposition|Merci d['’]avoir lu|Merci de votre lecture"
    ),
)

ES_PACK = build_pack(
    meta=(
        r"Como (?:modelo de lenguaje|modelo de IA|inteligencia artificial|asistente de IA)\b|"
        r"Este documento (?:tiene como objetivo|pretende|busca|tiene por objeto)|"
        r"En (?:esta|este) (?:sección|artículo|documento|guía),? (?:vamos a|veremos|exploraremos|analizaremos|abordaremos)|"
        r"^(?:En conclusión|En resumen|Para concluir|Para resumir|En definitiva)\b"
    ),
    filler=(
        r"Es (?:importante|fundamental|esencial|crucial|vital) (?:destacar|señalar|mencionar|resaltar|notar|tener en cuenta|recordar) que|"
        r"Cabe (?:destacar|señalar|mencionar|resaltar|recalcar) que|Vale la pena (?:destacar|mencionar|señalar|resaltar)|"
        r"Es digno de mención|Ni que decir tiene|Como (?:todos|bien) sabemos|"
        r"En el (?:mundo|panorama|entorno|ámbito|escenario) (?:actual|digital|tecnológico|de hoy)|En la era digital|"
        r"En el (?:acelerado|vertiginoso|dinámico) mundo|"
        r"(?:sumergirnos|sumergirse|adentrarnos|adentrarse|sumérgete|adéntrate) en|"
        r"sin lugar a dudas|\brevolucion(?:ar|ará|a|an|ario|aria)\b|de vanguardia|sin fisuras|"
        r"un verdadero testimonio|un testimonio de|en constante evolución"
    ),
    overclaim=(
        r"garantizado sin|riesgo cero|cero riesgos?|sin (?:ningún|ninguno) riesgo|"
        r"absolutamente (?:seguro|infalible|fiable)|infalible|nunca falla"
    ),
    closer=(
        r"Espero que (?:esto|esta información|esta guía|este documento|esta respuesta) (?:te |le |les )?"
        r"(?:sea útil|ayude|sirva|haya (?:sido )?útil|resulte útil)|"
        r"Espero que te (?:sirva|ayude)|"
        r"No (?:dudes|dude|duden) en (?:contactar|preguntar|consultar|escribir|comunicarte|ponerte)|"
        r"Gracias por (?:leer|tu lectura|su lectura)|Quedo a (?:tu|su) disposición"
    ),
)

LANG_PACKS: dict[str, tuple[Pattern, ...]] = {
    "universal": UNIVERSAL_PACK,
    "zh": ZH_PACK,
    "en": EN_PACK,
    "ja": JA_PACK,
    "ko": KO_PACK,
    "de": DE_PACK,
    "fr": FR_PACK,
    "es": ES_PACK,
    "ru": (),
    "pt": (),
}
ALL_LANGS = tuple(lang for lang in LANG_PACKS if lang != "universal")

ZH_DOC_ONLY_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "exclamation",
        re.compile(r"[!！]"),
        "装饰性感叹号；技术文档默认零感叹号，面向新用户的一句欢迎除外",
    ),
    (
        "conversational",
        re.compile(
            r"你会发现|其实[，,、。]|说白了|换句话说[，,]|"
            r"(?<![你我他])(?<!如果)(?<!假如)(?<!倘若)我们(?![的])"
            r"(?!\s*(?:不|不仅|建议|推荐|可以|需要|应该|必须|使用|选择|采用|"
            r"看到|发现|把|会|要|已|还|都|就|只|没))|"
            r"you will find that|basically,|to put it simply",
            re.IGNORECASE,
        ),
        "中文文档禁用无依据的「我们…」断言与对话化表达",
    ),
    (
        "buzzword",
        re.compile(
            r"赋能|助力|打造|一站式|深入浅出|"
            r"强大的|优雅的|无缝的|功能强大|"
            r"开箱即用(?![的])(?=，|。|、|！|？|$)",
        ),
        "中文文档禁用无依据的营销词",
    ),
)

CONTRAST_DIAGNOSTIC = re.compile(r"故障|问题|错误|缺陷|异常|失败|原因|配置|瓶颈|根因|Bug|bug")

def rhetorical_contrast(text: str) -> bool:
    for match in re.finditer(r"(?:这|它|该方案|此方案)?(?:并)?不是([^。！？\n]{1,24})而是", text):
        if not CONTRAST_DIAGNOSTIC.search(match.group(1)):
            return True
    for match in re.finditer(r"并非([^。！？\n]{1,24})而是", text):
        if not CONTRAST_DIAGNOSTIC.search(match.group(1)):
            return True
    return False

INLINE_CODE = re.compile(r"(?<!`)(`+)(?!`)(?:(?!`)\1(?!`)|.)*?(?<!`)\1(?!`)")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+")
LIST_ITEM = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+")
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
BLOCKQUOTE = re.compile(r"^\s*>")
REF_LINK_DEF = re.compile(r"^\s*\[[^\]]+\]:\s+\S+")
HR_LINE = re.compile(r"^\s{0,3}(?:={2,}|-{3,}|\*{3,}|_{3,})\s*$")
ABBREV = re.compile(
    r"\b(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|vs|etc|No|Fig|Vol|Rev|Approx|Dept|Inc|Ltd|Co)\.|"
    r"\b(?:e\.g|i\.e|U\.S|U\.K|a\.m|p\.m)\.|"
    r"\b(?:z\. ?B|d\. ?h|u\. ?a|u\. ?U|i\. ?d\. ?R|o\. ?Ä|s\. ?o|s\. ?u|z\. ?T|v\. ?a|p\. ?ex|p\. ?ej|EE\. ?UU)\.|"
    r"\b(?:bzw|usw|ca|vgl|Nr|Abb|evtl|ggf|inkl|zzgl|Mme|Mlle|cf|Sra|Srta|Dra|Ud|Uds|pág|núm|aprox)\.|"
    r"\b\d{1,2}\.(?=\s+(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\b)|"
    r"\bv?\d+(?:\.\d+)+",
    re.IGNORECASE,
)
ORDINAL_BEFORE_LOWERCASE = re.compile(r"\b\d+\.(?=\s+[a-zäöüß])")
GUILLEMETS = re.compile(r"«[^»]*»")
SENTINEL = "\ue000"
QUOTE_MASK = str.maketrans({".": "\ue000", "!": "\ue001", "?": "\ue002", ";": "\ue003"})
QUOTE_UNMASK = str.maketrans({"\ue000": ".", "\ue001": "!", "\ue002": "?", "\ue003": ";"})
SENTENCE_BREAK = re.compile(r"(?<=[。！？；!?;])|(?<=\.)(?=\s+)|(?<=…)(?=\s+[A-ZÀ-ÖØ-ÞА-ЯЁ])")

README_KINDS = ("readme",)

LATIN_LINE_LIMIT = 140
LATIN_SENTENCE_LIMIT = 90

PROFILES = {
    "general": {
        "max_line": 140,
        "max_sentence": 90,
        "max_paragraph": 8,
        "langs": ALL_LANGS,
        "extra_patterns": (),
        "readme_budget": None,
    },
    "zh-doc": {
        "max_line": 120,
        "max_sentence": 40,
        "max_paragraph": 4,
        "langs": ("zh",),
        "extra_patterns": ZH_DOC_ONLY_PATTERNS,
        "readme_budget": (120, 800),
    },
}

@dataclass
class Finding:
    path: str
    line: int
    column: int
    category: str
    excerpt: str
    hint: str
    severity: str = "advisory"

    def __post_init__(self) -> None:
        self.severity = SEVERITY_BY_ID.get(self.category, "advisory")

MD_ANCHOR = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
INLINE_URL = re.compile(r"<?https?://[^\s)>]+>?")

EXEMPT_PHRASES = re.compile(
    r"\b(?:nahtlos\w*|hochmodern\w*)\s+(?:Migration|Übergang|Integration|Überleitung|Wechsel|Anbindung|Anlage|System|Technik|Architektur|Infrastruktur)|"
    r"最先端の.{0,12}(?:技術|実装|手法|設計|アルゴリズム|世代)|"
    r"シームレスな.{0,12}(?:統合|移行|連携|接続)|"
    r"최첨단\s*(?:기술|장비|설비|공정|알고리즘)|"
    r"sans couture\s+(?:de|des|du|d['’]|entre|avec)|"
    r"de vanguardia\s+(?:en|para|del|de la)"
)

def strip_inline_code(line: str) -> str:
    without_code = INLINE_CODE.sub("", line)
    without_links = INLINE_URL.sub("", MD_ANCHOR.sub(r"\1", without_code))
    return EXEMPT_PHRASES.sub(" ", without_links)

def prose_of(raw: str) -> str:
    """Prose for scanning: strip inline code, links (keep anchor text), bare
    URLs, leftover tags and single-line HTML comments. Shared by scan_file,
    prose_text and parity so pattern hits and language detection always see
    the same text."""
    return NON_PROSE.sub(" ", strip_inline_code(raw))

def split_sentences(text: str) -> list[str]:
    protected = ABBREV.sub(lambda m: m.group(0).replace(".", SENTINEL), text)
    protected = ORDINAL_BEFORE_LOWERCASE.sub(lambda m: m.group(0).replace(".", SENTINEL), protected)
    protected = GUILLEMETS.sub(lambda m: m.group(0).translate(QUOTE_MASK), protected)
    parts = SENTENCE_BREAK.split(protected)
    return [p.translate(QUOTE_UNMASK).strip() for p in parts if p.strip()]

def count_cjk(text: str) -> int:
    return sum(1 for ch in text if "一" <= ch <= "鿿")

def count_kana(text: str) -> int:
    return sum(1 for ch in text if "぀" <= ch <= "ゟ" or "゠" <= ch <= "ヿ")

def count_hangul(text: str) -> int:
    return sum(1 for ch in text if "가" <= ch <= "힯" or "ᄀ" <= ch <= "ᇿ")

def count_east_asian(text: str) -> int:
    return count_cjk(text) + count_kana(text) + count_hangul(text)

def count_wide(text: str) -> int:
    """Double-width East Asian characters: han, kana, hangul syllables and
    jamo, CJK punctuation (U+3000–U+303F) and fullwidth forms (U+FF01–U+FF5E)."""
    return sum(1 for ch in text if (
        "一" <= ch <= "鿿"
        or "぀" <= ch <= "ヿ"
        or "가" <= ch <= "힯"
        or "ᄀ" <= ch <= "ᇿ"
        or "　" <= ch <= "〿"
        or "！" <= ch <= "～"
    ))

def has_cjk(text: str) -> bool:
    return any("一" <= ch <= "鿿" for ch in text)

LATIN_STOPWORDS = {
    "en": frozenset("the and of to is are for with that this it on as be by or not from can will if in at".split()),
    "de": frozenset("der die das und ist nicht mit für von zu den ein eine auf auch wird sich dem des im als bei oder wenn nur noch werden".split()),
    "fr": frozenset("le la les de des du un une et est que qui dans pour pas sur avec ce cette sont au aux ne se plus par".split()),
    "es": frozenset("el la los las de del que y en un una es se por con para no como más pero su al lo le".split()),
    "pt": frozenset("o a os as de do da dos das que e em um uma é se por com para não como mais mas você são está também".split()),
}
LATIN_DIACRITICS = {
    "de": ("äöüß", 2),
    "fr": ("èêàâçœùûîô«»", 2),
    "es": ("ñ", 2),
    "pt": ("ãõ", 2),
}
SPANISH_MARKS = "¿¡"
NON_PROSE = re.compile(r"https?://\S+|\]\([^)]*\)|<[^>]+>")
SCRIPT_WEIGHT = 3

def latin_language(text: str) -> str:
    folded = text.casefold()
    words = re.findall(r"[^\W\d_]+", folded)
    scores = {lang: sum(1 for word in words if word in stop) for lang, stop in LATIN_STOPWORDS.items()}
    for lang, (chars, weight) in LATIN_DIACRITICS.items():
        scores[lang] += weight * sum(folded.count(ch) for ch in chars)
    scores["es"] += 3 * sum(folded.count(ch) for ch in SPANISH_MARKS)
    best = max(scores.values())
    if best == 0:
        return "en"
    for lang in ("en", "de", "fr", "es", "pt"):
        if scores[lang] == best:
            return lang
    return "en"

def detect_language(text: str) -> str:
    cjk = count_cjk(text) + count_kana(text)
    hangul = count_hangul(text)
    cyrillic = sum(1 for ch in text if "Ѐ" <= ch <= "ӿ")
    latin = sum(1 for ch in text if ch.isalpha() and ord(ch) < 0x250)
    weighted = {
        "cjk": cjk * SCRIPT_WEIGHT,
        "ko": hangul * SCRIPT_WEIGHT,
        "ru": cyrillic,
        "latin": latin,
    }
    top = max(weighted, key=weighted.__getitem__)
    if weighted[top] == 0:
        return "en"
    if top == "cjk":
        return "ja" if count_kana(text) * 5 >= cjk else "zh"
    if top == "latin":
        return latin_language(text)
    return top

def frontmatter_length(lines: list[str]) -> int:
    if lines and lines[0].strip() == "---":
        for index, line in enumerate(lines[1:], start=2):
            if line.strip() == "---":
                return index
    return 0

# ---------------------------------------------------------------------------
# Line classification: fences, HTML comments, RST blocks.
# ---------------------------------------------------------------------------

FENCE_LINE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")

def classify_lines(lines: list[str], rst: bool = False) -> set[int]:
    """Line numbers whose content must never be treated as prose.

    Covers fenced code blocks (delimiter + interior), multi-line HTML
    comments and, for .rst, comment/directive blocks and literal blocks.
    Fence state is a proper parser: it records the fence character and the
    opening length; a fence only closes on a run of the same character at
    least as long as the opener with nothing else on the line, and an
    unclosed fence extends to end of file (CommonMark). ``~~~`` never closes
    a backtick fence and vice versa, so ``~~~`` section underlines in RST
    are handled by the rst branch instead.
    """
    if rst:
        return rst_excluded_lines(lines)
    excluded: set[int] = set()
    open_char = ""
    open_len = 0
    in_comment = False
    for number, raw in enumerate(lines, start=1):
        if open_char:
            excluded.add(number)
            match = FENCE_LINE.match(raw)
            if (match and match.group(1)[0] == open_char
                    and len(match.group(1)) >= open_len
                    and not match.group(2).strip()):
                open_char = ""
            continue
        if in_comment:
            excluded.add(number)
            if "-->" in INLINE_CODE.sub("", raw):
                in_comment = False
            continue
        match = FENCE_LINE.match(raw)
        if match:
            char, length = match.group(1)[0], len(match.group(1))
            if not (char == "`" and "`" in match.group(2)):
                open_char, open_len = char, length
                excluded.add(number)
            continue
        searchable = INLINE_CODE.sub("", raw)
        if "<!--" in searchable and "-->" not in searchable[searchable.find("<!--") + 4:]:
            in_comment = True
            excluded.add(number)
    return excluded

def rst_excluded_lines(lines: list[str]) -> set[int]:
    """RST comments (``..`` blocks, including indented directive content)
    and literal blocks (a paragraph ending in ``::`` followed by an indented
    block). ``~~~`` / ``===`` section underlines are left visible; they are
    filtered as structural rows, not swallowed as fence interiors."""
    excluded: set[int] = set()
    mode = ""
    pending_literal = False
    for number, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if mode:
            if not stripped or raw[:1] in " \t":
                excluded.add(number)
                continue
            mode = ""
        if stripped.startswith(".."):
            mode = "directive"
            excluded.add(number)
            continue
        if pending_literal:
            if not stripped:
                continue
            if raw[:1] in " \t":
                mode = "literal"
                pending_literal = False
                excluded.add(number)
                continue
            pending_literal = False
        if stripped.endswith("::") and not stripped.startswith(".."):
            pending_literal = True
    return excluded

def prose_text(lines: list[str], rst: bool = False) -> str:
    excluded = classify_lines(lines, rst)
    start = frontmatter_length(lines)
    kept: list[str] = []
    for number, raw in enumerate(lines, start=1):
        if number <= start or number in excluded or REF_LINK_DEF.match(raw):
            continue
        kept.append(prose_of(raw))
    return "\n".join(kept)

def read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError(f"文件不是有效 UTF-8 文本：{path}") from exc

def resolve_language(profile: str, lang: str, lines: list[str], rst: bool = False) -> str:
    available = PROFILES[profile]["langs"]
    if lang != "auto":
        if lang not in available:
            raise ValueError(f"profile {profile} 不包含语言包 {lang}（可用：{', '.join(available)}）")
        return lang
    detected = detect_language(prose_text(lines, rst))
    return detected if detected in available else ""

def measure(text: str, cjk_limit: int, latin_limit: int) -> tuple[int, int]:
    """Return (count, limit) under the documented counting standard.

    Counting standard (see docs/linter.md), in half-width units:
    - East Asian chars (han, kana, hangul syllables and jamo) weigh 2.
    - CJK punctuation and fullwidth forms (。、「」！＂～…) weigh 0, matching
      the historic behaviour where a 40-han sentence ending in 。 passed.
    - Every remaining character (Latin letters, digits, spaces, halfwidth
      punctuation) weighs 1. Pure Latin text therefore keeps the historic
      ``len()`` count, and pure Chinese keeps the historic han-only count.

    Mixed text counts BOTH parts: this fixes the old behaviour where a
    sentence containing a single han character was measured by its han count
    only, letting long English sentences slip through the Chinese budget.

    Budget: Japanese or Korean text uses the wide Latin budget doubled (long
    inflected words need more characters — 90 chars keep working). Otherwise
    the budget follows the dominant script: East-Asian-dominant (2×EA ≥
    narrow) uses the CJK budget doubled, so 40 han chars keep the old limit;
    Latin-dominant text with stray CJK chars uses the plain Latin budget.
    """
    han = count_cjk(text)
    kana = count_kana(text)
    hangul = count_hangul(text)
    ea = han + kana + hangul
    wide_punct = count_wide(text) - ea
    narrow = len(text) - count_wide(text)
    if ea == 0 and wide_punct == 0:
        return len(text), latin_limit
    count = 2 * ea + narrow
    if (hangul and hangul >= han) or (kana and kana * 5 >= han + kana):
        return count, 2 * latin_limit
    if 2 * ea >= narrow:
        return count, 2 * cjk_limit
    return count, latin_limit

def collect_files(inputs: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for raw in inputs:
        path = Path(raw)
        if not path.exists():
            raise FileNotFoundError(f"路径不存在：{path}")
        if path.is_dir():
            for candidate in path.rglob("*"):
                if not candidate.is_file() or candidate.suffix.lower() not in TEXT_SUFFIXES:
                    continue
                relative = candidate.relative_to(path)
                if any(part.startswith(".") for part in relative.parts[:-1]):
                    continue
                files.append(candidate)
        elif path.is_file():
            if path.suffix.lower() not in TEXT_SUFFIXES:
                raise ValueError(f"不支持的文件类型：{path}（支持：{', '.join(sorted(TEXT_SUFFIXES))}）")
            files.append(path)
    return sorted(set(files), key=lambda p: str(p))

def is_readme(path: Path) -> bool:
    stem = path.stem.lower()
    return any(stem == kind or stem.startswith(f"{kind}-") or stem.startswith(f"{kind}_")
               for kind in README_KINDS)

def scan_file(
    path: Path,
    *,
    profile: str,
    max_line: int,
    max_sentence: int,
    max_paragraph: int,
    extra_ignore: re.Pattern[str] | None = None,
    lang: str = "auto",
) -> list[Finding]:
    spec = PROFILES[profile]
    lines = read_lines(path)
    rst = path.suffix.lower() == ".rst"
    active = resolve_language(profile, lang, lines, rst)
    patterns = LANG_PACKS["universal"] + LANG_PACKS.get(active, ())
    if active == "zh" or profile == "zh-doc":
        patterns = patterns + LANG_PACKS["en"]
    if active == "zh":
        patterns = patterns + spec["extra_patterns"]

    findings: list[Finding] = []
    excluded = classify_lines(lines, rst)
    paragraph_lines: list[int] = []
    seen_prose: dict[str, int] = {}
    frontmatter_end = frontmatter_length(lines)

    def close_paragraph() -> None:
        nonlocal paragraph_lines
        if len(paragraph_lines) > max_paragraph:
            findings.append(Finding(
                str(path), paragraph_lines[0], 1, "long-paragraph",
                f"{len(paragraph_lines)} 行",
                f"连续段落超过 {max_paragraph} 行；确认是否包含多个信息点",
            ))
        paragraph_lines = []

    for number, raw in enumerate(lines, start=1):
        if number <= frontmatter_end:
            continue
        if number in excluded:
            close_paragraph()
            continue
        if extra_ignore and extra_ignore.search(raw):
            close_paragraph()
            continue

        prose = prose_of(raw).strip()
        if not prose:
            close_paragraph()
            continue

        is_heading = HEADING.match(raw) is not None
        is_table = TABLE_ROW.match(raw) is not None
        is_list = LIST_ITEM.match(raw) is not None
        is_quote = BLOCKQUOTE.match(raw) is not None
        is_ref = REF_LINK_DEF.match(raw) is not None
        is_hr = HR_LINE.match(raw) is not None
        structural = is_heading or is_table or is_list or is_quote or is_ref or is_hr

        if is_quote or is_hr:
            close_paragraph()
            continue
        if structural:
            close_paragraph()
        else:
            paragraph_lines.append(number)
            normalized = re.sub(r"\s+", " ", prose).casefold()
            long_enough = len(normalized) >= 24 or count_east_asian(normalized) >= 12
            first = seen_prose.get(normalized)
            if first is not None and long_enough:
                findings.append(Finding(
                    str(path), number, 1, "repeated-line", prose[:100],
                    f"与第 {first} 行正文重复；确认是否有意复用",
                ))
            else:
                seen_prose.setdefault(normalized, number)

        if not structural:
            line_len, line_limit = measure(prose, max_line, LATIN_LINE_LIMIT)
            if line_len > line_limit:
                findings.append(Finding(
                    str(path), number, 1, "long-line", f"{line_len} 字符",
                    f"超过 {line_limit} 字符；仅在影响阅读时拆分，不要破坏命令或结构",
                ))
            for sentence in split_sentences(prose):
                sent_len, sent_limit = measure(sentence, max_sentence, LATIN_SENTENCE_LIMIT)
                if sent_len > sent_limit:
                    findings.append(Finding(
                        str(path), number, 1, "long-sentence",
                        sentence[:72] + ("…" if len(sentence) > 72 else ""),
                        f"单句超过 {sent_limit} 字符；检查是否包含多个独立信息点",
                    ))

        for category, pattern, hint in patterns:
            match = pattern.search(prose)
            if match:
                findings.append(Finding(
                    str(path), number, match.start() + 1, category,
                    match.group(0)[:100], hint,
                ))

        if profile == "zh-doc" and active == "zh" and rhetorical_contrast(prose):
            findings.append(Finding(
                str(path), number, 1, "contrast",
                prose[:100],
                "中文文档禁用对仗句式；直接说后半句，排障结论除外",
            ))

    close_paragraph()

    budget = spec["readme_budget"]
    if budget and is_readme(path):
        line_budget, char_budget = budget
        body = lines[frontmatter_end:]
        if len(body) > line_budget:
            findings.append(Finding(
                str(path), 1, 1, "readme-line-budget", f"{len(body)} 行",
                f"中文文档模式：README 主体预算 {line_budget} 行；删除低价值内容，不要改格式规避",
            ))
        cjk = count_cjk("\n".join(body))
        if cjk > char_budget:
            findings.append(Finding(
                str(path), 1, 1, "readme-char-budget", f"{cjk} 个中文字符",
                f"中文文档模式：README 中文字符预算 {char_budget}；删除低价值内容，不要改格式规避",
            ))

    return findings

def parity_prose_lines(path: Path) -> list[tuple[int, str]]:
    lines = read_lines(path)
    rst = path.suffix.lower() == ".rst"
    excluded = classify_lines(lines, rst)
    start = frontmatter_length(lines)
    result: list[tuple[int, str]] = []
    for number, raw in enumerate(lines, start=1):
        if number <= start or number in excluded:
            continue
        result.append((number, prose_of(raw)))
    return result

def _number_sort_key(token: str) -> tuple[int, str]:
    return (0, f"{int(token):016d}") if token.isdigit() else (1, token)

def parity_findings(main: Path, pair: Path) -> list[Finding]:
    findings: list[Finding] = []

    def structure(path: Path) -> tuple[Counter, int]:
        lines = read_lines(path)
        rst = path.suffix.lower() == ".rst"
        excluded = classify_lines(lines, rst)
        headings: Counter = Counter()
        tables = 0
        start = frontmatter_length(lines)
        for number, raw in enumerate(lines, start=1):
            if number <= start or number in excluded:
                continue
            heading = re.match(r"^\s{0,3}(#{1,6})\s", raw)
            if heading:
                headings[len(heading.group(1))] += 1
            elif TABLE_ROW.match(raw):
                tables += 1
        return headings, tables

    main_headings, main_tables = structure(main)
    pair_headings, pair_tables = structure(pair)

    for level in sorted(set(main_headings) | set(pair_headings)):
        have, want = main_headings.get(level, 0), pair_headings.get(level, 0)
        if have != want:
            findings.append(Finding(
                str(main), 1, 1, "parity-heading",
                f"{'#' * level} 主×{have} 对照×{want}",
                f"与 {pair.name} 的 {level} 级标题数不一致；确认是否漏了小节",
            ))

    if main_tables != pair_tables:
        findings.append(Finding(
            str(main), 1, 1, "parity-table",
            f"表格行 主×{main_tables} 对照×{pair_tables}",
            f"与 {pair.name} 的表格行数不一致；确认命令或条目是否漏译",
        ))

    main_prose = parity_prose_lines(main)
    pair_prose = parity_prose_lines(pair)

    def tokens(items: list[tuple[int, str]]) -> Counter:
        counter: Counter = Counter()
        for _, text in items:
            counter.update(re.findall(r"\d+", text))
        return counter

    main_tokens, pair_tokens = tokens(main_prose), tokens(pair_prose)

    def first_line(items: list[tuple[int, str]], needle: str) -> int:
        return next((number for number, text in items if needle in text), 1)

    for token in sorted(set(main_tokens) | set(pair_tokens), key=_number_sort_key):
        have, want = main_tokens.get(token, 0), pair_tokens.get(token, 0)
        if have == want:
            continue
        findings.append(Finding(
            str(main), first_line(main_prose, token), 1, "parity-number",
            f"「{token}」主×{have} 对照×{want}",
            f"与 {pair.name} 的正文数字不一致；确认哪边与实现相符（代码块与行内代码不计）",
        ))

    return findings

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Advisory quality linter for Markdown and plain text.")
    parser.add_argument("paths", nargs="+", help="Markdown / plain-text files or directories")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="general",
                        help="规则集：general（跨领域）或 zh-doc（中文文档硬纪律）")
    parser.add_argument("--lang", choices=["auto", *ALL_LANGS], default="auto",
                        help="语言包：auto（按文档主语言检测，默认）或强制指定；zh-doc 只含 zh")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--strict", action="store_true",
                       help="发现任意问题时返回退出码 1（等价 --fail-on advisory）")
    group.add_argument("--fail-on", choices=("advisory", "warning", "error", "none"), default=None,
                       help="返回退出码 1 的最低严重程度（advisory=任何提示）；默认不因提示改变退出码")
    parser.add_argument("--max-line", type=int, help="行长阈值；默认 general 140 / zh-doc 120")
    parser.add_argument("--max-sentence", type=int, help="句长阈值；默认 general 90 / zh-doc 40")
    parser.add_argument("--max-paragraph", type=int, help="段落行数阈值；默认 general 8 / zh-doc 4")
    parser.add_argument("--ignore-regex", help="忽略匹配此正则的整行（跳过该行全部检查）")
    parser.add_argument("--pair", action="append", default=None, metavar="FILE",
                        help="对照语言对（如 README.zh-CN.md）；可重复，逐一与第一个路径比较标题、表格行与正文数字")
    return parser

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    spec = PROFILES[args.profile]
    max_line = args.max_line if args.max_line is not None else spec["max_line"]
    max_sentence = args.max_sentence if args.max_sentence is not None else spec["max_sentence"]
    max_paragraph = args.max_paragraph if args.max_paragraph is not None else spec["max_paragraph"]
    if min(max_line, max_sentence, max_paragraph) < 1:
        parser.error("长度阈值必须大于 0")
    threshold = SEVERITY_RANK.get(args.fail_on, 0) if args.fail_on else (1 if args.strict else 0)

    try:
        files = collect_files(args.paths)
        if not files:
            raise ValueError("没有找到支持的文本文件")
        if args.pair and len(files) != 1:
            raise ValueError("--pair 需要恰好一个主文件作为对照基准")
        pair_paths: list[Path] = []
        if args.pair:
            for raw in args.pair:
                pair = Path(raw)
                if not pair.is_file():
                    raise FileNotFoundError(f"对照文件不存在或不是文件：{pair}")
                if pair.suffix.lower() not in TEXT_SUFFIXES:
                    raise ValueError(f"不支持的对照文件类型：{pair}")
                pair_paths.append(pair)
        ignore = re.compile(args.ignore_regex) if args.ignore_regex else None
        findings: list[Finding] = []
        languages: dict[str, str] = {}
        for path in files:
            rst = path.suffix.lower() == ".rst"
            languages[str(path)] = (args.lang if args.lang != "auto"
                                    else detect_language(prose_text(read_lines(path), rst)))
            findings.extend(scan_file(
                path,
                profile=args.profile,
                max_line=max_line,
                max_sentence=max_sentence,
                max_paragraph=max_paragraph,
                extra_ignore=ignore,
                lang=args.lang,
            ))
        for pair in pair_paths:
            findings.extend(parity_findings(files[0], pair))
    except (OSError, ValueError, re.error) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({
            "profile": args.profile,
            "languages": languages,
            "files_scanned": len(files),
            "finding_count": len(findings),
            "severity_counts": {name: sum(1 for item in findings if item.severity == name)
                                for name in ("error", "warning", "advisory")},
            "findings": [asdict(item) for item in findings],
            "note": "Findings are review candidates, not automatic proof of bad writing.",
        }, ensure_ascii=False, indent=2))
    else:
        print(f"profile: {args.profile}")
        for path in files:
            count = sum(item.path == str(path) for item in findings)
            print(f"{path}: {count} 条提示")
        for item in findings:
            print(f"  {item.path}:{item.line}:{item.column} [{item.category}/{item.severity}] {item.excerpt}")
            print(f"    {item.hint}")
        if pair_paths:
            print(f"语言对对照：{', '.join(str(pair) for pair in pair_paths)}")
        counts = Counter(item.severity for item in findings)
        summary = f"扫描 {len(files)} 个文件，发现 {len(findings)} 条提示"
        if findings:
            summary += f"（error {counts.get('error', 0)} / warning {counts.get('warning', 0)} / advisory {counts.get('advisory', 0)}）"
        print(summary + "。")
        if not findings:
            print("未发现已配置模式；这不代表事实或整体质量已通过审核。")

    return 1 if threshold and any(SEVERITY_RANK.get(item.severity, 1) >= threshold for item in findings) else 0

if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build the site-wide search index and specialty (科別) map for the homepage.

Run from anywhere after adding or editing notes:

    python3 tools/build_search_index.py

Writes two files at the repo root:
  search-meta.js   — every page's title, series and specialties (loaded with the homepage)
  search-index.js  — section headings + text for full-text search (loaded on first search)

New pages are picked up automatically from `git ls-files`. Give a new page its
specialties in SPECS below (or rely on its folder's default in FOLDER_SPECS).
"""
import html
import json
import os
import re
import subprocess
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# 科別：key → (名稱, 圖示, 顏色, 分組[, 上層科別])，順序即首頁顯示順序；沒有筆記的科別會以灰色「尚無」顯示
# 有上層科別的（如 腎臟、泌尿 → 腎臟泌尿）只標子科別即可，上層會自動加上
SPECIALTIES = [
    ('cardio',   '心臟',         '🫀', '#DC2626', '專科'),
    ('heme',     '血液與輸血',   '🩸', '#B91C1C', '專科'),
    ('onc',      '腫瘤',         '🎗️', '#9333EA', '專科'),
    ('ecc',      '急診重症',     '🚑', '#EA580C', '專科'),
    ('surg',     '外科',         '🔪', '#0E7490', '專科'),
    ('ophtho',   '眼科',         '👁️', '#2563EB', '專科'),
    ('endo',     '內分泌',       '🧪', '#0F766E', '內科'),
    ('renal',    '腎臟泌尿',     '💧', '#0284C7', '內科'),
    ('kidney',   '腎臟',         '🫘', '#0369A1', '內科', 'renal'),
    ('uro',      '泌尿',         '🚻', '#0891B2', '內科', 'renal'),
    ('gi',       '腸胃消化',     '🍽️', '#A16207', '內科'),
    ('resp',     '呼吸',         '🫁', '#7C3AED', '內科'),
    ('infect',   '感染與抗生素', '🧫', '#5B3EBD', '內科'),
    ('nutrition','營養與肥胖',   '🥣', '#65A30D', '內科'),
    ('us',       '超音波',       '🔊', '#0F5E9C', '影像'),
    ('clinpath', '臨床病理',     '🔬', '#4F46E5', '基礎與技能'),
    ('skills',   '臨床技能與病歷','📝', '#475569', '基礎與技能'),
]

# 系列：資料夾 → 系列名稱、首頁卡片連結
SERIES = {
    'texas-endocrine-2026':    '2026 Texas 內分泌研討會',
    'tsfm-feline-ecc-2026':    '2026 TSFM 貓急重症研討會',
    'echocardiography':        '心臟超音波系列（ESAVS）',
    'case-discussions':        '梅醫師病例討論',
    'antimicrobial-selection': '知菌知藥：抗菌藥物選擇',
    'lulich-urology-2026':     'Jody Lulich 泌尿講座',
    'rita-ho-oncology-2026':   'Rita Ho 腫瘤科講座',
    'ultrasound':              '超音波專區',
    'notes':                   '單篇筆記',
}

FOLDER_SPECS = {
    'texas-endocrine-2026': ['endo'],
    'tsfm-feline-ecc-2026': ['ecc'],
    'echocardiography':     ['cardio', 'us'],
    'ultrasound':           ['us'],
    'antimicrobial-selection': ['infect'],
    'lulich-urology-2026':  ['uro'],
    'rita-ho-oncology-2026': ['onc'],
}

SPECS = {
    'texas-endocrine-2026/endocrine-neoplasia.html': ['endo', 'onc'],
    'texas-endocrine-2026/hypercalcemia.html':       ['endo', 'onc'],
    'echocardiography/14-pericardial-effusion.html': ['cardio', 'onc', 'us'],
    'ultrasound/feline-biliary-tree.html':           ['us', 'gi'],
    'lulich-urology-2026/feline-urethral-obstruction.html': ['uro', 'ecc'],
    'lulich-urology-2026/feline-nephroureterolithiasis.html': ['uro', 'kidney'],
    'texas-endocrine-2026/pupd.html':                ['endo', 'kidney'],
    'texas-endocrine-2026/dka-hhs.html':             ['endo', 'ecc'],
    'texas-endocrine-2026/diabetic-nutrition.html':  ['endo', 'nutrition'],
    'texas-endocrine-2026/obesity-weight-loss.html': ['endo', 'nutrition'],
    'tsfm-feline-ecc-2026/aki.html':                 ['ecc', 'kidney'],
    'tsfm-feline-ecc-2026/bleeding-transfusion.html':['ecc', 'heme'],
    'tsfm-feline-ecc-2026/cant-breathe-localization.html': ['ecc', 'resp'],
    'tsfm-feline-ecc-2026/cant-breathe-next.html':   ['ecc', 'resp'],
    'tsfm-feline-ecc-2026/dka-diabetes.html':        ['ecc', 'endo'],
    'tsfm-feline-ecc-2026/fate.html':                ['ecc', 'cardio'],
    'tsfm-feline-ecc-2026/sepsis.html':              ['ecc', 'infect'],
    'case-discussions/canine-juvenile-thyroid-growth-retardation.html': ['endo'],
    'case-discussions/feline-chf-fluid-intolerance.html': ['cardio', 'kidney'],
    'case-discussions/feline-chronic-diarrhea.html': ['gi'],
    'case-discussions/feline-chronic-vomiting.html': ['gi'],
    'case-discussions/feline-ckd-obesity-enteropathy.html': ['kidney', 'gi', 'nutrition'],
    'case-discussions/feline-hypercalcemia-luts.html': ['uro', 'kidney', 'endo'],
    'case-discussions/feline-severe-uri-outdoor-cat.html': ['resp', 'infect'],
    'antimicrobial-selection/part1.html':            ['infect', 'uro'],
    'antimicrobial-selection/part2.html':            ['infect', 'resp'],
    'notes/blood-transfusion.html':                  ['heme', 'ecc'],
    'notes/clinical-pathology.html':                 ['clinpath', 'kidney'],
    'notes/feline-diabetes.html':                    ['endo'],
    'notes/hospitalized-care.html':                  ['skills', 'ecc'],
    'notes/soap-note-template.html':                 ['skills'],
    'poster.html':                                   ['heme'],
}

# 有密碼保護的系列：只收標題，不收內文
GATED = ('echocardiography/',)

SKIP_TAGS = {'head', 'title', 'script', 'style', 'noscript', 'svg', 'template'}
HEADINGS = {'h1', 'h2', 'h3'}


class Extractor(HTMLParser):
    """Split a page into sections at each h2/h3; anchor = heading id or nearest ancestor id."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []          # (tag, id, skip)
        self.sections = []
        self.cur = {'id': '', 'h': '', 't': []}
        self.in_heading = None
        self.heading_buf = []

    def skipping(self):
        return any(s for _, _, s in self.stack)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        skip = tag in SKIP_TAGS or a.get('id') == 'sidebar' or 'home-link-fab' in (a.get('class') or '')
        void = tag in ('br', 'img', 'hr', 'input', 'meta', 'link', 'source', 'col', 'wbr')
        if tag in HEADINGS and not self.skipping():
            self.flush()
            anchor = a.get('id') or next((i for _, i, _ in reversed(self.stack) if i and i not in ('main',)), '')
            self.cur = {'id': anchor, 'h': '', 't': []}
            self.in_heading = tag
            self.heading_buf = []
        if not void:
            self.stack.append((tag, a.get('id'), skip))

    def handle_endtag(self, tag):
        if self.in_heading == tag:
            self.cur['h'] = norm(''.join(self.heading_buf))
            self.in_heading = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self.skipping():
            return
        if self.in_heading:
            self.heading_buf.append(data)
        else:
            if data.strip() not in ('▾', '▸', '→', '←'):
                self.cur['t'].append(data)

    def flush(self):
        text = norm(' '.join(self.cur['t']))
        if text or self.cur['h']:
            self.sections.append({'id': self.cur['id'], 'h': self.cur['h'], 't': text})


def norm(s):
    return re.sub(r'\s+', ' ', html.unescape(s)).strip()


def clean_title(t):
    t = norm(t)
    t = re.split(r'\s*[｜|]\s*', t)[0]
    return t.lstrip('🩸 ').strip()


def series_of(path):
    top = path.split('/')[0] if '/' in path else ''
    return top, SERIES.get(top, '單篇筆記')


PARENT = {row[0]: row[5] for row in SPECIALTIES if len(row) > 5}


def main():
    files = subprocess.run(['git', 'ls-files', '*.html'], capture_output=True, text=True, check=True).stdout.split()
    pages, sections = [], []
    for path in sorted(files):
        if path == 'index.html':
            continue
        src = open(path, encoding='utf-8').read()
        m = re.search(r'<title>(.*?)</title>', src, re.S)
        title = clean_title(m.group(1)) if m else path
        folder, series = series_of(path)
        is_index = path.endswith('/index.html')
        specs = list(SPECS.get(path) or FOLDER_SPECS.get(folder) or [])
        for k in list(specs):
            if PARENT.get(k) and PARENT[k] not in specs:
                specs.append(PARENT[k])
        pages.append({'u': path, 'title': title, 'series': series, 'folder': folder,
                      'specs': [] if is_index else specs, 'index': is_index,
                      'gated': path.startswith(GATED)})
        if path.startswith(GATED):
            continue
        ex = Extractor()
        ex.feed(src)
        ex.flush()
        for s in ex.sections:
            if len(s['t']) < 2 and not s['h']:
                continue
            sections.append([len(pages) - 1, s['id'], s['h'], s['t']])

    meta = {'specialties': [{'key': r[0], 'name': r[1], 'icon': r[2], 'color': r[3], 'group': r[4],
                                    **({'parent': r[5]} if len(r) > 5 else {})} for r in SPECIALTIES],
            'series': SERIES, 'pages': pages}
    with open('search-meta.js', 'w', encoding='utf-8') as f:
        f.write('// 由 tools/build_search_index.py 產生，請勿手動修改\n')
        f.write('window.VN_META = ' + json.dumps(meta, ensure_ascii=False, separators=(',', ':')) + ';\n')
    with open('search-index.js', 'w', encoding='utf-8') as f:
        f.write('// 由 tools/build_search_index.py 產生，請勿手動修改\n')
        f.write('window.VN_INDEX = ' + json.dumps(sections, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f'{len(pages)} pages, {len(sections)} sections, '
          f'meta {os.path.getsize("search-meta.js")//1024} KB, index {os.path.getsize("search-index.js")//1024} KB')


if __name__ == '__main__':
    main()

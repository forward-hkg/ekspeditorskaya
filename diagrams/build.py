#!/usr/bin/env python3
"""Диаграммы лендинга: один источник для отдельных HTML-файлов и для вставки в public/index.html.

Запуск: python3 diagrams/build.py
- пишет diagrams/<slug>.html (самодостаточные файлы по правилам навыка diagram-design);
- заменяет в public/index.html содержимое между <!-- diagram:<slug> --> и <!-- /diagram:<slug> -->.

Оформление — токены лендинга (public/assets/css/tokens.css): бумага, чернила, жёлтый маркер, IBM Plex.
Цвета в SVG заданы классами, поэтому на странице диаграммы берут значения из tokens.css.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / 'public' / 'index.html'
OUT = ROOT / 'diagrams'

# ---------- примитивы ----------


def node(x, y, w, h, lines, sub=None, kind='step', rx=6):
    """Узел: непрозрачная подложка, рамка, 1–2 строки названия и техническая подпись."""
    cx = x + w / 2
    n = len(lines)
    block = n * 15 + (13 if sub else 0)
    top = y + (h - block) / 2 + 11
    out = [f'<rect class="dg-mask" x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"/>',
           f'<rect class="dg-node dg-node--{kind}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"/>']
    for i, line in enumerate(lines):
        out.append(f'<text class="dg-name" x="{cx}" y="{top + i * 15}" text-anchor="middle">{line}</text>')
    if sub:
        out.append(f'<text class="dg-sub" x="{cx}" y="{top + n * 15 + 1}" text-anchor="middle">{sub}</text>')
    return '\n'.join(out)


def diamond(cx, cy, w, h, lines):
    pts = f'{cx},{cy - h / 2} {cx + w / 2},{cy} {cx},{cy + h / 2} {cx - w / 2},{cy}'
    out = [f'<polygon class="dg-mask" points="{pts}"/>', f'<polygon class="dg-node dg-node--step" points="{pts}"/>']
    top = cy - (len(lines) * 15) / 2 + 11
    for i, line in enumerate(lines):
        out.append(f'<text class="dg-name" x="{cx}" y="{top + i * 15}" text-anchor="middle">{line}</text>')
    return '\n'.join(out)


def arrow(d, slug, dashed=False):
    cls = 'dg-arrow dg-arrow--dashed' if dashed else 'dg-arrow'
    return f'<path class="{cls}" d="{d}" marker-end="url(#{slug}-arrow)"/>'


def label(x, y, text, anchor='middle'):
    """Подпись стрелки на подложке. (x, y) — базовая линия текста."""
    w = round(len(text) * 6.2 + 12)
    rx = x - w / 2 if anchor == 'middle' else (x - 6 if anchor == 'start' else x - w + 6)
    return (f'<rect class="dg-mask" x="{rx}" y="{y - 11}" width="{w}" height="15" rx="2"/>'
            f'<text class="dg-label" x="{x}" y="{y}" text-anchor="{anchor}">{text}</text>')


def legend(y, width, items):
    out = [f'<line class="dg-rule" x1="24" y1="{y - 8}" x2="{width - 24}" y2="{y - 8}"/>']
    x = 24
    for kind, text in items:
        out.append(f'<rect class="dg-node dg-node--{kind}" x="{x}" y="{y + 2}" width="16" height="12" rx="2"/>')
        out.append(f'<text class="dg-sub" x="{x + 24}" y="{y + 12}">{text}</text>')
        x += 24 + round(len(text) * 6.2) + 32
    return '\n'.join(out)


def svg(slug, w, h, title, desc, body):
    return f'''<svg class="dg" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{slug}-title {slug}-desc">
<title id="{slug}-title">{title}</title>
<desc id="{slug}-desc">{desc}</desc>
<defs>
<marker id="{slug}-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon class="dg-head" points="0 0, 8 3, 0 6"/></marker>
</defs>
{body}
</svg>'''


# ---------- 1. Задача: кто что делает (swimlane) ----------

def tasks():
    slug, W, H = 'dg-tasks', 1000, 408
    lanes = [('Постановщик', 40), ('Система', 140), ('Исполнитель', 240)]
    b = []
    for i, (name, y) in enumerate(lanes):
        b.append(f'<line class="dg-rule" x1="24" y1="{y}" x2="976" y2="{y}"/>')
        b.append(f'<text class="dg-lane" x="24" y="{y + 54}">{name}</text>')
    b.append('<line class="dg-rule" x1="24" y1="340" x2="976" y2="340"/>')
    # стрелки — до узлов, чтобы линии ушли под рамки
    b += [
        arrow('M252,90 H332 Q340,90 340,98 V157', slug),
        arrow('M396,190 H476 Q484,190 484,198 V257', slug),
        arrow('M540,290 H571', slug),
        arrow('M628,258 V123', slug),
        arrow('M684,90 H764 Q772,90 772,98 V257', slug),
        arrow('M828,290 H908 Q916,290 916,282 V223', slug),
        label(642, 194, 'вопрос', 'start'),
        label(786, 194, 'ответ', 'start'),
    ]
    b += [
        node(140, 58, 112, 64, ['Ставит задачу', 'из карточки'], 'статус: новая', 'focal'),
        node(284, 158, 112, 64, ['Уведомляет', 'участников'], 'Email, Max', 'system'),
        node(428, 258, 112, 64, ['Берёт в работу'], 'статус: в работе'),
        node(572, 258, 112, 64, ['Задаёт вопрос', 'в комментариях'], 'ждёт ответа'),
        node(572, 58, 112, 64, ['Отвечает', 'в комментариях']),
        node(716, 258, 112, 64, ['Закрывает', 'задачу'], 'статус: выполнена'),
        node(860, 158, 112, 64, ['Ставит дату', 'завершения'], 'письмо автору', 'system'),
    ]
    b.append(legend(372, W, [('focal', 'задача создаётся из карточки записи'), ('step', 'действие сотрудника'), ('system', 'действие системы')]))
    return slug, svg(slug, W, H, 'Путь задачи: постановщик, система, исполнитель',
                     'Постановщик ставит задачу из карточки, система уведомляет участников, исполнитель берёт её в работу, '
                     'уточняет детали в комментариях и закрывает; система ставит дату завершения и сообщает постановщику.',
                     '\n'.join(b)), 'Swimlane', 'Путь задачи: кто что делает'


# ---------- 2. Доступ: откроется ли запись (flowchart) ----------

def access():
    slug, W, H = 'dg-access', 616, 620
    b = []
    cx = 220
    b += [
        arrow(f'M{cx},72 V99', slug),
        arrow(f'M{cx},180 V219', slug),
        arrow(f'M{cx},300 V339', slug),
        arrow(f'M{cx},420 V459', slug),
        # отказы уходят вправо, у каждого своя точка входа на общем узле
        arrow('M340,140 H492 Q500,140 500,148 V227', slug),
        arrow('M340,260 H411', slug),
        arrow('M340,380 H492 Q500,380 500,372 V293', slug),
        label(360, 130, 'нет', 'start'),
        label(360, 250, 'нет', 'start'),
        label(360, 370, 'нет', 'start'),
        label(cx + 12, 204, 'да', 'start'),
        label(cx + 12, 324, 'да', 'start'),
        label(cx + 12, 444, 'да', 'start'),
    ]
    b += [
        node(140, 24, 160, 48, ['Сотрудник открывает', 'перевозку'], rx=24),
        diamond(cx, 140, 240, 80, ['Есть доступ', 'к разделу?']),
        diamond(cx, 260, 240, 80, ['Его организация', 'и офис?']),
        diamond(cx, 380, 240, 80, ['Он ответственный', 'или открыты все?']),
        node(140, 460, 160, 56, ['Карточка открыта'], 'финансы — отдельно', 'focal', rx=24),
        node(412, 228, 176, 64, ['Запись не видна'], 'ни в списке, ни по ссылке', 'system', rx=24),
    ]
    b.append(f'<text class="dg-sub" x="24" y="548">Уровень раздела и разрешения берутся у сотрудника,</text>')
    b.append(f'<text class="dg-sub" x="24" y="562">а если не заданы — у его группы.</text>')
    b.append(legend(590, W, [('focal', 'доступ есть'), ('system', 'доступа нет'), ('step', 'проверка')]))
    return slug, svg(slug, W, H, 'Как система решает, откроется ли перевозка сотруднику',
                     'Три проверки подряд: уровень доступа к разделу, организация и офис записи, участие сотрудника как ответственного '
                     'или право видеть все записи. Если все пройдены, карточка открывается; финансовые поля требуют отдельного разрешения.',
                     '\n'.join(b)), 'Flowchart', 'Откроется ли запись сотруднику'


# ---------- 3. Вайб: слои системы (layer stack) ----------

def layers():
    slug, W, H = 'dg-layers', 1000, 372
    rows = [
        ('слой 4', 'Доработки вашей компании', 'поля, отчёты, фильтры, уведомления, правила доступа', 'меняют ваши сотрудники', 'focal'),
        ('слой 3', 'Экспедиторская', 'котировки, перевозки, документы, финансы, обмен с 1С и ЭДО', 'обновляется новыми версиями', 'step'),
        ('слой 2', 'Платформа', 'права, журнал изменений, задачи, комментарии, ИИ-помощник', 'обновляется новыми версиями', 'step'),
        ('слой 1', 'Открытые технологии', 'PHP, Laravel, MySQL', 'бесплатные и открытые', 'system'),
    ]
    b = []
    y = 24
    for tag, name, what, who, kind in rows:
        b.append(f'<rect class="dg-mask" x="120" y="{y}" width="856" height="64"/>')
        b.append(f'<rect class="dg-node dg-node--{kind}" x="120" y="{y}" width="856" height="64"/>')
        b.append(f'<text class="dg-sub" x="136" y="{y + 37}">{tag}</text>')
        b.append(f'<text class="dg-layer" x="208" y="{y + 30}">{name}</text>')
        b.append(f'<text class="dg-sub" x="208" y="{y + 48}">{what}</text>')
        b.append(f'<text class="dg-sub" x="960" y="{y + 37}" text-anchor="end">{who}</text>')
        y += 64
    # направление: доработки лежат поверх и не меняют нижние слои
    b.append(arrow('M72,272 V33', slug))
    b.append('<text class="dg-sub" x="24" y="300">доработки —</text>')
    b.append('<text class="dg-sub" x="24" y="314">поверх ядра</text>')
    b.append(legend(336, W, [('focal', 'слой доработок: хранится отдельно и переживает обновления'), ('step', 'ядро системы'), ('system', 'основа')]))
    return slug, svg(slug, W, H, 'Слои системы: доработки лежат поверх ядра',
                     'Четыре слоя снизу вверх: открытые технологии, платформа, отраслевые разделы «Экспедиторской» и слой доработок компании. '
                     'Доработки хранятся отдельно, поэтому нижние слои обновляются новыми версиями.',
                     '\n'.join(b)), 'Layer stack', 'Слои системы'


# ---------- 4. Входящий счёт: от получения до оплаты или спора (flowchart) ----------

def invoices():
    slug, W, H = 'dg-invoices', 1000, 366
    b = []
    b += [
        # два канала входят в один узел — у каждого своя точка на его левой грани
        arrow('M152,68 H176 Q184,68 184,76 V88 Q184,96 192,96 H215', slug),
        arrow('M152,152 H176 Q184,152 184,144 V132 Q184,124 192,124 H215', slug),
        arrow('M368,110 H399', slug),
        arrow('M600,110 H659', slug),
        arrow('M804,110 H851', slug),
        arrow('M500,158 V225', slug),
        arrow('M408,258 H300 Q292,258 292,250 V147', slug, dashed=True),
        label(612, 100, 'да', 'start'),
        label(512, 196, 'нет', 'start'),
        label(304, 206, 'исправленный документ', 'start'),
    ]
    b += [
        node(24, 40, 128, 56, ['Почта'], 'счёт или УПД в PDF', 'system'),
        node(24, 124, 128, 56, ['ЭДО'], 'Диадок, Saby', 'system'),
        node(216, 74, 152, 72, ['Счёт или УПД', 'заведён в системе'], 'распознан из PDF/XML'),
        diamond(500, 110, 200, 96, ['Логист проверяет:', 'всё верно?']),
        node(660, 78, 144, 64, ['Выгрузка в 1С'], 'учёт в бухгалтерии', 'focal'),
        node(852, 78, 124, 64, ['Оплата'], 'заявка на оплату'),
        node(408, 226, 184, 64, ['Оспаривание (dispute)'], 'переписка и статус в системе'),
    ]
    b.append(legend(330, W, [('focal', 'в 1С уходят только принятые документы'), ('step', 'работа в системе'), ('system', 'канал получения')]))
    return slug, svg(slug, W, H, 'Путь входящего счёта и УПД',
                     'Счёт или УПД перевозчика приходит по почте или через ЭДО — оба канала работают параллельно. Документ заводится в системе, '
                     'логист проверяет его. Принятый документ выгружается в 1С и идёт на оплату. Некорректный переходит к оспариванию: '
                     'переписка и статус ведутся в системе, исправленный документ возвращается на проверку.',
                     '\n'.join(b)), 'Flowchart', 'Путь входящего счёта и УПД'


# ---------- вывод ----------

CSS = '''
    .dg { display: block; width: 100%; height: auto; }
    .dg text { font-family: var(--font-body); fill: var(--color-ink); }
    .dg-mask { fill: var(--dg-ground, var(--color-paper)); }
    .dg-node { stroke-width: 1; }
    .dg-node--step { fill: var(--color-sheet); stroke: var(--color-ink); }
    .dg-node--focal { fill: var(--color-accent); stroke: var(--color-ink); stroke-width: 1.5; }
    .dg-node--system { fill: var(--color-paper-2); stroke: var(--color-ink-3); }
    .dg-name { font-size: 12px; font-weight: 600; }
    .dg-layer { font-size: 15px; font-weight: 600; }
    .dg .dg-sub, .dg .dg-label, .dg .dg-lane { font-family: var(--font-mono); fill: var(--color-ink-2); }
    .dg-sub { font-size: 9.5px; }
    .dg-label { font-size: 10px; }
    .dg .dg-lane { font-size: 11px; font-weight: 500; fill: var(--color-ink); }
    .dg-rule { stroke: var(--color-rule); stroke-width: 1; }
    .dg-arrow { fill: none; stroke: var(--color-ink-2); stroke-width: 1.2; }
    .dg-arrow--dashed { stroke-dasharray: 5 4; }
    .dg-head { fill: var(--color-ink-2); }
'''

PAGE = '''<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wdth,wght@75..100,400..700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --color-paper: oklch(98.8% 0.003 100);
      --color-paper-2: oklch(95.6% 0.006 100);
      --color-sheet: oklch(100% 0 0);
      --color-ink: oklch(20% 0.008 100);
      --color-ink-2: oklch(40% 0.008 100);
      --color-ink-3: oklch(52% 0.008 100);
      --color-rule: oklch(87% 0.006 100);
      --color-accent: oklch(90% 0.175 98);
      --font-body: "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif;
      --font-mono: "IBM Plex Mono", ui-monospace, monospace;
    }}
    body {{ font-family: var(--font-body); background: var(--color-paper); color: var(--color-ink); padding: 3rem 2rem; }}
    .frame {{ max-width: {maxw}px; margin: 0 auto; }}
    .eyebrow {{ font-family: var(--font-mono); font-size: 0.75rem; color: var(--color-ink-2); margin-bottom: 0.5rem; }}
    h1 {{ font-size: 1.75rem; font-weight: 600; font-stretch: 80%; line-height: 1.15; margin-bottom: 1.5rem; }}
{css}  </style>
</head>
<body>
  <div class="frame">
    <p class="eyebrow">{kind} — Экспедиторская</p>
    <h1>{title}</h1>
{svg}
  </div>
</body>
</html>
'''


def main():
    html = INDEX.read_text(encoding='utf-8')
    for build in (tasks, access, layers, invoices):
        slug, code, kind, title = build()
        maxw = int(re.search(r'viewBox="0 0 (\d+)', code).group(1)) + 200
        (OUT / f'{slug}.html').write_text(PAGE.format(title=title, kind=kind, css=CSS, svg=code, maxw=maxw), encoding='utf-8')
        pat = re.compile(rf'(<!-- diagram:{slug} -->\n).*?(\n\s*<!-- /diagram:{slug} -->)', re.S)
        if pat.search(html):
            html = pat.sub(lambda m: m.group(1) + code + m.group(2), html)
            print('embedded', slug)
        else:
            print('no placeholder for', slug)
    INDEX.write_text(html, encoding='utf-8')


if __name__ == '__main__':
    main()

import os, re

os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open('AGENTS.md', 'r', encoding='utf-8') as f:
    content = f.read()

# ── 1. Tree diagram ──
v = '\u2502'
t = '\u251c'
b = '\u2514'
h = '\u2500'

old_1 = (
    v + '   ' + v + '   ' + v + '   ' + t + h + h + ' <slug>.json        <-          Manifiesto: lista de secciones\n'
    + v + '   ' + v + '   ' + v + '   ' + b + h + h + ' sections/          <-          Archivos de secci\u00f3n individuales\n'
    + v + '   ' + v + '   ' + t + h + h + ' plans/                 <-       plan.json gen
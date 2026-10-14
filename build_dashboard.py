from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/'outputs'/'dashboard_data.json').read_text())
data['maps']=json.loads((ROOT/'outputs'/'map_data.json').read_text())
template=(ROOT/'dashboard_template.html').read_text()
for placeholder,name in [('__MAP_STYLE__','map_style.css'),('__MAP_PANEL__','map_panel.html')]:
    assert template.count(placeholder)==1
    template=template.replace(placeholder,(ROOT/name).read_text())
assert template.count('__MAP_JS__')==1
template=template.replace('__MAP_JS__',(ROOT/'map_core.js').read_text()+'\n'+(ROOT/'map_ui.js').read_text())
assert template.count('__DATA__')==1
output=ROOT/'NYC_Restaurant_Explorer.html'
output.write_text(template.replace('__DATA__',json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')),encoding='utf-8')
(ROOT/'index.html').write_bytes(output.read_bytes())
print(output)
print(ROOT/'index.html')

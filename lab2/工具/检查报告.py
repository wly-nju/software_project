from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
from pypdf import PdfReader
import json
r=Path(__file__).resolve().parents[1];d=r/'过程记录/报告预览'
pages=sorted(d.glob('page-*.png'))
for j in range(0,len(pages),4):
    sheet=Image.new('RGB',(1040,1500),'#e5e9ee');draw=ImageDraw.Draw(sheet)
    for k,p in enumerate(pages[j:j+4]):
        im=Image.open(p).convert('RGB');im.thumbnail((500,715));x=(k%2)*520+(520-im.width)//2;y=(k//2)*750+25
        sheet.paste(im,(x,y));draw.text(((k%2)*520+15,(k//2)*750+5),p.stem,fill='black')
    sheet.save(d/f'sheet-{j//4+1:02}.jpg',quality=87)
reader=PdfReader(r/'报告/build/实验报告.pdf');info=[]
for i,p in enumerate(reader.pages):
    t=p.extract_text() or '';info.append({'page':i+1,'text_length':len(t),'head':t[:100].replace('\n',' '),'rotation':p.get('/Rotate',0),'images':len(p.images)})
(r/'过程记录/报告页面检查.json').write_text(json.dumps({'pages':len(reader.pages),'page_info':info,'scope':'排版核对辅助；仍须查看渲染图'},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(info,ensure_ascii=True))

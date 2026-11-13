"""Validate design deliverables and build the course ZIP. Does not mutate Git."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,zipfile,xml.etree.ElementTree as ET
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=ROOT.parents[2]
def sha(data):return hashlib.sha256(data).hexdigest()
trace=json.loads((ROOT/'过程记录/需求设计追踪.json').read_text(encoding='utf-8'))
ids=[r[0] for r in trace['requirements']]
assert sorted(ids)==[f'REQ-{i:03}' for i in range(1,41)]
pumls=sorted((ROOT/'UML').glob('*.puml'));assert len(pumls)==11
assert {p.stem for p in pumls}=={p.stem for p in (ROOT/'UML').glob('*.png')}
kindcounts={k:sum(k in p.stem for p in pumls) for k in ['组件图','用例图','类图','状态图','时序图','部署图']}
assert all(n>0 for n in kindcounts.values())
for p in pumls:
    t=p.read_text(encoding='utf-8');assert '@startuml' in t and '@enduml' in t
uis=sorted((ROOT/'UI界面').glob('*.png'));assert len(uis)==29
catalog=json.loads((ROOT/'UI界面/界面目录.json').read_text(encoding='utf-8'));assert len(catalog)==28
covered={m for s in catalog for m in s['module'].split('/')}
assert covered=={f'M{i:02}' for i in range(1,12)}
boards=ET.parse(ROOT/'UI界面/原型/票遇界面设计.drawio').getroot().findall('diagram')
assert len(boards)==29
assert all(len(b.findall('.//mxCell'))>20 for b in boards)
prototype=json.loads((ROOT/'过程记录/原型自动检查.json').read_text(encoding='utf-8'))
assert len(prototype['checks'])==7 and not prototype['errors'] and not prototype['layout']
srcpdf=ROOT/'报告/build/实验报告.pdf';assert srcpdf.exists()
reader=PdfReader(srcpdf);text='\n'.join(p.extract_text() or '' for p in reader.pages)
for key in ['项目概况','模块划分','类图','状态图','时序图','UI','AI','待本人最终审查']:
    assert key in text,key
image_count=sum(len(p.images) for p in reader.pages)
assert image_count==40,image_count
assert all((p.extract_text() or '').strip() or len(p.images) for p in reader.pages)
log=(ROOT/'报告/build/实验报告.log').read_text(encoding='utf-8',errors='replace')
assert not re.search(r'Overfull|Missing character|undefined references|Rerun to get',log)
repo=ROOT.parent
expected_tags={'lab1-ai-draft':'cb366d6a57a2ea7fc2088f27f3ff931ccbee1207','lab1-final':'ad83340e2cab6b91488b7a5732da7141c9088e41'}
for tag,expected in expected_tags.items():
    actual=subprocess.check_output(['git','-C',str(repo),'rev-parse',f'{tag}^{{commit}}'],text=True).strip();assert actual==expected
mainpdf=ROOT/'报告/实验报告.pdf';shutil.copy2(srcpdf,mainpdf)
out=WORKSPACE/'output/lab2';out.mkdir(parents=True,exist_ok=True)
outer='实验2_241820015_万连勇';archive=out/(outer+'.zip')
# Keep source/image pairs explicit; no JSON, prototype, build files or process records in the submission archive.
files=[(mainpdf,'实验报告.pdf')]+[(p,'UML/'+p.name) for p in sorted((ROOT/'UML').glob('*')) if p.suffix in ['.puml','.png']]+[(p,'UI界面/'+p.name) for p in uis]
manifest=[]
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p,name in files:
        data=p.read_bytes();z.writestr(outer+'/'+name,data);manifest.append({'path':outer+'/'+name,'sha256':sha(data),'bytes':len(data)})
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None and len(z.namelist())==52
    assert all(sha(z.read(m['path']))==m['sha256'] for m in manifest)
result={'date':'2026-11-13','stage':'完整AI设计稿，待本人最终审查','requirements':len(ids),'modules':len(covered),'uml_types':kindcounts,'uml_png':len(pumls),'ui_png':len(uis),'editable_boards':len(boards),'pdf_pages':len(reader.pages),'pdf_image_instances':image_count,'prototype_checks':prototype['checks'],'zip':str(archive),'zip_file_count':len(files),'zip_sha256':sha(archive.read_bytes()),'lab1_tags_unchanged':True,'git_committed':False,'human_review':'尚待本人实际审查','validation_scope':'设计覆盖、实际渲染、原型交互、PDF版式与ZIP逐文件一致性；非后端验收','files':manifest}
(ROOT/'过程记录/交付核对.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
done=f'''# 本轮完成清单

日期：2026年11月13日。状态：**完整AI设计稿已完成，待本人最终审查。**

## 已完成的内容

1. 核对实验一固定需求基线，建立40条需求的模块、UML、UI与质量设计追踪，覆盖11个逻辑模块。
2. 完成模块化单体、分层、应用接口、实体/表关系、唯一约束、容量守恒、事务/幂等、敏感字段及历史保存设计。
3. 绘制六种UML共11张：1组件图、2类图、1部署图、2用例图、1状态图、4时序图；全部保留puml与PNG。
4. 设计29张UI，覆盖参与者、组织者、检票人员与管理员，以及注册、选座、候补、退票、转赠锁定、离线、异常、统计及审计。
5. 保留HTML/CSS/JS可点击原型、29页可编辑draw.io画板、导出及重建工具。UI不是完整业务软件。
6. 编写{len(reader.pages)}页实验报告，包含架构理由、所有UML、全部29张UI、AI过程/优缺点/修改及工作流反思、实验总结和40条追踪附录。保留LaTeX正文与编译说明，无页眉页脚。
7. 追加AI-002～006实际辅助过程，保留AI-001原始文件和首次图形结果；补齐人工审查模板与检查顺序。
8. 制定性能、安全、可靠性、易用性和关键异常的后续验收计划。
9. 按课程命名和目录生成ZIP，包内仅报告、UML源/图、UI图，共52个文件，逐文件SHA-256与工作目录对应文件一致。

## 已做的检查

- 40条需求、11模块、六种UML覆盖和源图配对检查。
- PlantUML实际渲染成功；29张UI实际导出；29页画板XML可解析且含独立可编辑对象。
- 28页与1状态无脚本异常/横向溢出，7项原型交互检查通过。
- PDF逐页渲染并核对布局，{image_count}次图像使用覆盖全部UML/UI；编译无溢出、缺字或未定义引用。
- ZIP可读取、结构正确、52文件内容一致；实验一两个固定标签完整提交编号未改变。

## 文件入口

- 报告：`报告/实验报告.pdf`；编辑：`报告/实验报告.tex`。
- 设计：`设计说明/01～04`；图：`UML/`；界面：`UI界面/`。
- 原型：`UI界面/原型/index.html`；画板：`UI界面/原型/票遇界面设计.drawio`。
- 提交包：`{archive}`。
- 检查证据：`过程记录/交付核对.json`；辅助过程：`AI使用记录.md`。

## 仍由本人完成

先保存完整AI稿Git提交，再进行真实人工审查，填写`人工审查记录.md`并修改相应源文件；补充报告中自己的体验、取舍和实际优化，保存人工修订提交。Git提交/推送继续由本人操作，命令见README。

人工修改后重新导出受影响图片、编译报告并运行打包工具。当前未执行后端实现、真实并发/安全/性能/恢复验收或用户测试；原需求中未决参数仍保留待澄清。AI自检不是人工修改证据。
'''
(ROOT/'完成清单.md').write_text(done,encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['files','prototype_checks']},ensure_ascii=True,indent=2))

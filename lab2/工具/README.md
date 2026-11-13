# 设计源文件与重建工具

## 环境

本机已使用PlantUML 1.2025.10、Azul Java17、Chrome、Playwright、Python及MiKTeX XeLaTeX导出。PlantUML来自官方发布的Maven制品，图形使用Smetana布局；中文采用Microsoft YaHei。Java和PlantUML放在工作区`.lab2-tools`，不打入作业包。

## UML

`生成UML.py`根据DIAGRAMS字典写11份puml，直接手改puml后不要重运行此脚本覆盖。单独运行以下命令重新渲染（在工作区根目录，路径可按安装位置调整）：

```powershell
& '.lab2-tools/zulu17.70.113-ca-jre17.0.21.0.3-win_x64/bin/java.exe' '-Dfile.encoding=UTF-8' -jar '.lab2-tools/plantuml.jar' -charset UTF-8 -tpng 'lab1/活动票务与报名系统/lab2/UML/*.puml'
```

## UI

在`UI界面/原型`中修改HTML/CSS/JS，浏览器直接打开index.html预览。`票遇界面设计.drawio`有29页可编辑画板，可在diagrams.net导入后独立修改；源文件基于实际控件、容器和文字导出，没有把整页截图放入画板冒充可编辑内容。

`导出界面.cjs`使用Playwright启动本机Chrome，保存29张PNG、界面目录、29页画板及7项交互检查JSON。脚本中node_modules为本机路径，其他机器需替换为自己的Playwright安装；运行前先保留手改过的画板，重新导出会覆盖。

## 文档和报告

`整理设计与报告.py`依据模块映射和界面目录生成设计说明03/04、追踪JSON及实验报告.tex，运行会覆盖这些文件；人工修改后优先直接编辑和编译。报告编译见`报告/编译说明.md`。`检查报告.py`将已渲染PDF汇成预览并记录页面索引；图像渲染使用本机Poppler。

## 检查与打包

`检查与打包.py`核对40条需求、11模块、六种UML、puml/PNG配对、29张UI、draw.io画板数、PDF内图像与关键章节，复制主PDF并按任务书结构构造ZIP，逐文件验证SHA-256。它不会提交Git、伪造人工审查或移动任何标签。

使用已安装Python运行对应脚本即可。ZIP输出在工作区`output/lab2`，大型临时预览和编译文件从Git排除。

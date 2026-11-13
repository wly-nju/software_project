// Export editable mxGraph/draw.io boards from the UI design prototype.
const fs=require('fs');
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll('\n','&#xa;');
async function captureBoard(page,s){
 const shapes=await page.evaluate(()=>{
  const shapes=[],rgb=c=>{if(!c||c==='transparent')return null;let m=c.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([.\d]+))?\)/);if(!m)return null;let a=m[4]===undefined?1:Number(m[4]);if(a===0)return null;return '#'+m.slice(1,4).map(v=>Math.round(Number(v)*a+255*(1-a)).toString(16).padStart(2,'0')).join('')};
  const rect=e=>{let b=e.getBoundingClientRect();return{x:b.x+scrollX,y:b.y+scrollY,w:b.width,h:b.height}};
  const root=document.querySelector('#app');
  for(const e of [root,...root.querySelectorAll('*')]){
   let b=rect(e),c=getComputedStyle(e);if(b.w<2||b.h<2||c.display==='none'||c.visibility==='hidden')continue;
   let fill=rgb(c.backgroundColor),stroke=parseFloat(c.borderTopWidth)>0?rgb(c.borderTopColor):null;
   if(c.backgroundImage!=='none'&&!fill)fill=e.classList.contains('hero')?'#40348c':'#eceaf8';
   if(fill||stroke)shapes.push({...b,fill,stroke,round:parseFloat(c.borderRadius)>3,text:''});
   if(['INPUT','TEXTAREA','SELECT'].includes(e.tagName)&&!['checkbox','password'].includes(e.type)){
    let val=e.tagName==='SELECT'?e.selectedOptions[0]?.textContent:e.value||e.placeholder;if(val)shapes.push({...b,x:b.x+10,w:b.w-20,text:val,font:parseFloat(c.fontSize),color:rgb(c.color),bold:false});
   }
   if(e.tagName==='INPUT'&&e.type==='password')shapes.push({...b,x:b.x+10,w:b.w-20,text:'••••••••',font:14,color:'#374151'});
   if(e.tagName==='INPUT'&&e.type==='checkbox'&&e.checked)shapes.push({...b,text:'✓',font:11,color:'#4f46e5',bold:true});
  }
  let walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT),n;
  while(n=walker.nextNode()){
   let t=n.textContent.trim(),p=n.parentElement;if(!t||['OPTION','STYLE','SCRIPT'].includes(p.tagName))continue;
   let c=getComputedStyle(p);if(c.visibility==='hidden'||c.display==='none')continue;let range=document.createRange();range.selectNodeContents(n);let rr=range.getBoundingClientRect();if(!rr.width||!rr.height)continue;
   shapes.push({x:rr.x+scrollX,y:rr.y+scrollY,w:rr.width+3,h:rr.height+2,text:t,font:parseFloat(c.fontSize),color:rgb(c.color),bold:Number(c.fontWeight)>=600});
  }
  return{width:innerWidth,height:document.documentElement.scrollHeight,shapes};
 });
 return{s,...shapes};
}
function saveBoards(boards,file){
 let xml='<?xml version="1.0" encoding="UTF-8"?>\n<mxfile host="app.diagrams.net" modified="2026-11-13T00:00:00.000Z" agent="UI design export" version="24.7.17" compressed="false">';
 for(let b of boards){xml+=`<diagram id="${esc(b.s.id)}" name="${esc(b.s.title)}"><mxGraphModel dx="${b.width}" dy="${b.height}" grid="0" page="1" pageScale="1" pageWidth="${b.width}" pageHeight="${b.height}" background="#f7f8fc"><root><mxCell id="0"/><mxCell id="1" parent="0"/>`;
  b.shapes.forEach((r,i)=>{let style=r.text?`text;html=0;align=left;verticalAlign=middle;whiteSpace=wrap;overflow=hidden;fillColor=none;strokeColor=none;fontFamily=Microsoft YaHei;fontSize=${r.font||13};fontColor=${r.color||'#111827'};fontStyle=${r.bold?1:0};spacing=0;`:`rounded=${r.round?1:0};arcSize=14;fillColor=${r.fill||'none'};strokeColor=${r.stroke||'none'};strokeWidth=1;`;xml+=`<mxCell id="c${i}" value="${esc(r.text)}" style="${esc(style)}" vertex="1" parent="1"><mxGeometry x="${r.x.toFixed(1)}" y="${r.y.toFixed(1)}" width="${r.w.toFixed(1)}" height="${r.h.toFixed(1)}" as="geometry"/></mxCell>`});
  xml+='</root></mxGraphModel></diagram>';
 }
 xml+='</mxfile>';fs.writeFileSync(file,xml);
}
module.exports={captureBoard,saveBoards};

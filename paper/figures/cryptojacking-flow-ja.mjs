import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
const base='C:/Users/ettotto/Desktop/mylife_skills/tmp/attack-flow-page1-2';
await fs.mkdir(base+'/output',{recursive:true});
const p=Presentation.create({slideSize:{width:1280,height:355}});
const s=p.slides.add();s.background.fill='#FFFFFF';
function text(name,value,x,y,w,h,size=26,bold=false,color='#17212B'){
 const a=s.shapes.add({geometry:'textbox',name,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 a.text=value;a.text.style={fontSize:size,typeface:'Meiryo',color,bold,alignment:'center',verticalAlignment:'middle',autoFit:'none',insets:0};return a;
}
function box(name,x,y,w,h,fill='#FFFFFF',stroke='#354351'){
 return s.shapes.add({geometry:'rect',name,position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width:2}});
}
function arrow(name,x,y,w,h,reverse=false){
 const a=s.shapes.add({geometry:'connector',name,kind:'straight',position:{left:x,top:y,width:w,height:h},line:{fill:'#354351',width:2},[reverse?'head':'tail']:{type:'triangle',width:'med',length:'med'}});return a;
}
box('配信元',12,42,268,200);
text('配信元見出し','Webページ',22,60,248,40,29,true);
text('配信コード','JavaScript＋Wasm\n難読化したWasmを含む',22,112,248,100,22);
box('ブラウザ',468,42,380,200);
text('ブラウザ見出し','利用者のブラウザ',478,54,360,43,29,true);
text('通信','JavaScript：通信・呼出し',478,103,360,38,24);
box('研究対象',482,151,352,78,'#ECF2F8','#24547A');
text('ハッシュ計算','③ Wasmでハッシュ計算\n利用者の同意なくCPUを使用',486,153,344,72,23,true,'#183E60');
box('プール',1030,42,238,200);
text('プール見出し','マイニングプール',1038,57,222,43,26,true);
text('プール説明','計算タスクを配分\n受信した結果を確認',1038,113,222,94,22);
text('配信ラベル','①ダウンロード\nさせる',286,63,176,65,23);
arrow('コード配信',285,137,177,0);
text('仕事ラベル','②計算タスク',852,62,172,40,23);
arrow('仕事受信',854,118,170,0,true);
text('結果ラベル','④結果を送信',852,162,172,40,23);
arrow('結果送信',854,217,170,0);
arrow('報酬',1150,246,0,39);
box('攻撃者',1030,291,238,53);
text('攻撃者報酬','⑤攻撃者に報酬',1036,294,226,44,24,true);
s.speakerNotes.text='Cabrera-Arteaga et al., WebAssembly diversification for malware evasion (2023), Section 3 and Figure 1: https://arxiv.org/pdf/2212.08427 . 原論文の攻撃シナリオを参考に，日本語で構成と配置を独自に作成した。利用者がWebページを開いた後の流れを示す。通信はJavaScriptが仲介し，Wasmはハッシュ計算を担う。報酬はマイニングプール側の条件に従う。研究対象は通信や検知器ではなくWasmのコードと計算である。';
await fs.writeFile(base+'/attack-flow-ja.png',new Uint8Array(await (await p.export({slide:s,format:'png',scale:2})).arrayBuffer()));
const sk='C:/Users/ettotto/.codex/plugins/cache/openai-primary-runtime/presentations/26.1020.11618/skills/presentations';
const {finalizePresentation}=await import(pathToFileURL(sk+'/container_tools/artifact_tool_utils.mjs').href);
const candidate=base+'/candidate.pptx';await (await PresentationFile.exportPptx(p)).save(candidate);
const result=await finalizePresentation({workspaceDir:base,candidatePath:candidate,finalPath:base+'/output/cryptojacking-flow-ja.pptx',pythonExecutable:'C:/Users/ettotto/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:sk+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:sk+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,3381375','--validate-heading-fit'],explicitTotalSlideCount:1,requiredNativeTableOwnerSlides:[],fontPolicy:{basis:'design',families:['Meiryo']},verifyArtifactToolImport:true,receiptPath:base+'/validation.json'});
console.log(JSON.stringify(result));

import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from 'file:///C:/Users/ettotto/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';

const ROOT='C:/Users/ettotto/Documents/webassembly_obfuscation';
const BUILD=path.join(ROOT,'tmp/daybreak-presentation-build');
const OUT=path.join(ROOT,'deliverables/daybreak-research-20261026');
const SKILL='C:/Users/ettotto/.codex/plugins/cache/openai-primary-runtime/presentations/26.1020.11618/skills/presentations';
const PY='C:/Users/ettotto/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
const FINAL=path.join(OUT,'Wasm研究_OpenAI_Daybreak申請相談.pptx');
const C={bg:'#F8FAFC',ink:'#142A42',body:'#30445A',muted:'#5F7185',teal:'#007E87',light:'#E4EBF1',white:'#FFFFFF'};
const F='Meiryo';
const p=Presentation.create({slideSize:{width:1280,height:720}});
function text(s,content,x,y,w,h,size=28,color=C.body,bold=false){
 const q=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 q.text=content;q.text.style={typeface:F,fontSize:size,color,bold,insets:0,autoFit:'none',wrap:'square',verticalAlignment:'top'};return q;
}
function slide(title,number){
 const s=p.slides.add();s.background.fill=C.bg;
 text(s,title,72,48,1136,100,44,C.ink,true);
 text(s,String(number).padStart(2,'0'),1170,666,48,30,20,C.muted);
 return s;
}
function table(s,values,y,widths,height){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:72,top:y,width:1136,height,columnWidths:widths,values});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=t.getCell(r,c);cell.fill=r===0?C.ink:C.white;
  cell.text.style={typeface:F,fontSize:24,color:r===0?C.white:C.body,bold:r===0,insets:14,verticalAlignment:'middle'};
 }
 t.borders.assign({style:'solid',fill:C.light,width:1});return t;
}
const official='https://help.openai.com/en/articles/20001258-openai-daybreak-trusted-access-for-cyber-overview';
const checks='https://help.openai.com/en/articles/20001326-additional-safety-checks-for-biological-and-cybersecurity-requests-in-chatgpt-codex-and-the-api';
const apply='https://openai.com/form/enterprise-trusted-access-for-cyber/';

// 1: A single request, without implying that access is assured.
{
 const s=p.slides.add();s.background.fill=C.ink;
 text(s,'Wasmセキュリティ研究の推進に向けた',72,112,1136,80,43,C.white);
 text(s,'OpenAI Daybreak\n利用申請の相談',72,210,1136,194,66,C.white,true);
 text(s,'研究室として申請できるか、利用・管理体制を含めて\nご相談したいと考えています。',76,454,1110,110,32,'#D9E7F0');
 text(s,'修士研究に向けた研究テーマ・実験環境の相談　2026年10月26日',76,644,1110,36,22,'#B7CCD9');
 s.speakerNotes.text='本日は、Wasmセキュリティの修士研究に向けて、OpenAI Daybreakの組織申請を検討できるか相談します。申請の承認、新規研究成果、費用の発生を既定事項とはしません。研究概要と利用計画は学生側で準備し、申請主体や学内の手続きについて先生のご助言をお願いする趣旨です。制度情報の確認日:2026-10-26。公式資料:'+official+'\n組織申請窓口:'+apply;
}
// 2: Explain the actual research problem and the change of direction.
{
 const s=slide('研究課題：実行負荷に見合う解析の難しさ',2);
 text(s,'当初の狙いは、正当なソフトウェアの知的財産を守るWasm難読化です。',72,158,1136,50,29,C.body);
 table(s,[
  ['既存手法で注意する点','問題が生じる仕組み','研究で確かめること'],
  ['複雑な見た目','最適化や処理の要約で簡単になる場合がある','同等の計算を回復する時間'],
  ['制御フローの隠蔽','値やメモリアクセスの関係が残る場合がある','演算・データ構造の回復費用'],
  ['保護を強める追加処理','実行時間・サイズ・メモリも増える','同じ実行負荷の方式との比較']
 ],234,[265,435,436],300);
 text(s,'現在はWasmセキュリティ全般へ広げ、GCのテスト入力生成も検討しています。',72,577,1110,72,27,C.teal,true);
 s.speakerNotes.text='既存難読化が一律に無効だという主張ではありません。目標は解析不能性ではなく、保護した処理やデータ構造を回復する費用を、実用的な実行負荷の範囲で増やすことです。WASMixerはWasm固有の制御フロー再構成等を扱います。NotDecは型とデータ構造の回復を進めていますが、同論文が全ての難読化を解除したという意味ではありません。現在のR案は難読化とは別方向の、GC値を構築して対象操作を実行するテスト生成研究です。\n先行資料: https://arxiv.org/abs/2308.03123 ; https://arxiv.org/abs/2608.03286\n内部根拠: research/evaluation-policy.md ; research/typed-relay/README.md ; research/gc-witness/results.md';
}
// 3: Researcher responsibility and concrete AI tasks.
{
 const s=slide('AIは、仮説を実装と反証へ進めるために使う',3);
 text(s,'AIに支援してもらう作業',72,171,530,60,32,C.teal,true);
 text(s,'先行論文・実装との技術的な比較\n\n変換器・テスト・実験スクリプトの実装\n\n境界値や反例の探索、測定結果の整理',72,254,545,264,27,C.body);
 text(s,'研究者が判断・確認すること',680,171,528,60,32,C.ink,true);
 text(s,'保護目標・攻撃モデル・成功条件\n\n動作の正しさ、比較の公平性、再現性\n\n新規性の主張と、結果の限界',680,254,528,264,27,C.body);
 text(s,'AIの提案を採用する前に、先行研究との照合と実測による検証を行います。',72,581,1136,70,28,C.teal,true);
 s.speakerNotes.text='AIを使う意義は、文献調査だけでなく実際のプログラムと反例検査へ進める速度にあります。研究上の判断、引用の正確性、実験条件と主張の範囲は人間が確認します。AIが生成した説明のもっともらしさを新規性の証拠にしません。実験で支持されない候補も負の結果として保存しています。内部根拠: research/evaluation-policy.md ; research/gc-witness/plan.md ; research/gc-witness/audit.py';
}
// 4: Actual results, explicitly limited to the current experiment.
{
 const s=slide('現在の到達点：実験基盤は動作、新規性は検証中',4);
 text(s,'965本',72,171,490,106,72,C.teal,true);
 text(s,'生成・検証したWasmバイナリ',76,282,515,46,26,C.body);
 text(s,'2,895回',685,171,520,106,72,C.ink,true);
 text(s,'3エンジンでの実行に成功',689,282,505,46,26,C.body);
 text(s,'対象：GC参照値の構築と、指定した参照アクセスの実行',72,359,1136,49,29,C.ink,true);
 table(s,[['生成方式','成功した課題数'],['通常のmemo化DFS','325 / 384'],['試作したworklist方式','325 / 384']],430,[760,376],159);
 text(s,'両方式の325出力は同一。主テーマとして十分な新規性は、まだ確立していません。',72,620,1100,50,23,C.body);
 s.speakerNotes.text='R案の限定実験です。86型構成・500型から384の対象型とアクセス経路の課題を作り、3方式の成功出力計965本を検証しました。Node、Wasmtime、SpiderMonkeyで計2,895実行が成功しました。これは965個の実アプリでも、全入力の数学的証明でもありません。強い比較対象のmemo化DFSも325課題を生成し、worklistとの325出力がbyte一致しました。実装と再現実験はありますが、新しい一般アルゴリズムの優位は得ていません。最新の追加実験では既存wasm-smithへの簡単な修正にも効果があり、R独自の効果の評価を継続しています。\n根拠: results/gc-witness/screen-v1/summary.json ; results/gc-witness/audit-v1/report.json ; research/gc-witness/results.md\n環境: Node24.15.0、Wasmtime Python50.0.1、SpiderMonkey150.0.1。';
}
// 5: State the need without inventing a history of blocks or time savings.
{
 const s=slide('研究用途と管理体制を示し、利用経路を整える',5);
 text(s,'難読化・逆解析・脆弱性検証は、正当な研究でも用途の説明が重要です。',72,165,1136,84,32,C.ink,true);
 text(s,'研究で必要な作業',72,283,300,42,27,C.teal,true);
 text(s,'解析への耐性評価、反例の作成、実装の差分検査',402,283,806,82,29,C.body);
 text(s,'申請で伝えること',72,391,300,42,27,C.teal,true);
 text(s,'大学・研究室での研究目的、許可対象、利用者と管理方法',402,391,806,82,29,C.body);
 text(s,'期待する効果',72,499,300,42,27,C.teal,true);
 text(s,'承認された用途に適したアクセス条件を確認し、\n実装と比較実験を継続しやすくする',402,499,806,112,29,C.body);
 text(s,'追加チェックや回答不可の件数・待ち時間による影響は、現時点では未集計です。',72,647,1100,34,20,C.muted);
 s.speakerNotes.text='OpenAIの公式説明では、サイバー関連の要求には追加の自動チェックが入り、応答が遅くなったり内容を返せなかったりすることがあります。チェック表示だけで規約違反と判断されたことにはなりません。ここで、特定の頻度で拒否された、何時間失った、申請後に何倍速くなるという未計測の主張はしません。申請の必要性は、研究用途を説明し、適切な承認と管理された利用経路を確認することです。\n公式根拠:'+checks+'\n制度説明:'+official;
}
// 6: Accurate institutional request; account-model applicability matters.
{
 const s=slide('Daybreakは、許可された研究用途の審査制アクセス',6);
 table(s,[
  ['項目','申請前に確認する内容'],
  ['Blue / Red','区分ごとに対象業務・モデル・承認条件が異なる'],
  ['モデルへの適用','使用中のモデルと、承認後の適用範囲を確認する'],
  ['組織としての適格性','大学・研究室の申請資格と申請名義を窓口に確認する'],
  ['承認後の設定','対象利用者・workspace・API projectの権限を設定する']
 ],170,[310,826],355);
 text(s,'承認後も利用規約と安全措置は継続します。全ての要求への回答は保証されません。',72,570,1136,78,27,C.ink,true);
 text(s,'制度・申請窓口はOpenAI公式資料で確認。2026年10月26日時点。',72,659,1100,30,20,C.muted);
 s.speakerNotes.text='公式概要は多くのチームにBlueを出発点として推奨していますが、Blueで全モデルの拒否が緩和されるわけではありません。2026-10-26に確認した表ではGPT-6.1 SolとAstraはBlueでは標準の安全措置、Redでは緩和対象です。Redは別途承認が必要で、組織の適格性も審査されます。本資料は研究室の資格、承認、価格を保証しません。Zero Data Retentionも自動で付与されません。承認されたworkspaceやprojectへの設定が必要です。\n公式根拠:'+official+'\n組織向け申請先:'+apply;
}
// 7: Concrete operation, scoped to this research and actual program requirements.
{
 const s=slide('初期利用は、研究室が管理する実験に限定する',7);
 table(s,[
  ['管理項目','初期運用の提案'],
  ['実験対象','自作Wasm、公開実装、利用条件と許可を確認した資料'],
  ['実行環境','ローカルの隔離環境。実行時間・資源使用量を制限'],
  ['利用者と情報','承認済み利用者ごとの権限。未公開情報の送信は事前確認'],
  ['研究の記録','コード、seed、ログ、比較条件、失敗例を保存'],
  ['公開・外部への働きかけ','研究室の方針と承認手続きに従って判断']
 ],170,[310,826],390);
 text(s,'研究の効率と再現性を、研究室の管理体制の下で評価します。',72,608,1136,60,29,C.teal,true);
 s.speakerNotes.text='個人アカウントや認証情報を共有する運用は提案していません。研究室として利用者を指定し、各自の権限で利用します。外部サービスや第三者環境の検査は、明示的な許可がある場合に限ります。公開コードでもlicenseと利用条件を確認します。未公開コードや共同研究データの送信可否は学内方針に従います。成果の外部公開や問題の報告は先生と相談します。\n制度上の利用範囲と管理権限の根拠:'+official+'\n研究の現状: research/gc-witness/README.md ; research/evaluation-policy.md';
}
// 8: A reviewable, specific ask with responsibilities.
{
 const s=slide('研究室として申請を検討してよいか、ご相談したい',8);
 text(s,'先生にご相談したいこと',72,175,1136,48,32,C.ink,true);
 text(s,'組織申請を進める可否と、大学・研究室の申請名義\n\n学内の確認先、管理担当者、対象利用者\n\n契約条件・費用を確認した上での利用予算',72,252,1136,223,29,C.body);
 text(s,'学生側で準備するもの',72,510,1136,43,29,C.teal,true);
 text(s,'研究概要、利用目的、対象範囲、実験計画、現状の記録をまとめた申請草案',72,568,1136,72,28,C.body);
 s.speakerNotes.text='最初のお願いは購入や契約の即決ではなく、組織申請を検討してよいかという判断です。学生側で草案と研究資料を用意し、先生には申請主体、学内手続き、管理体制についてご相談したいと考えています。申請資格、対応モデル、アクセス区分、費用と契約条件を確認してから利用方針を決めます。\n申請窓口:'+apply+'\n公式制度説明:'+official;
}

await fs.mkdir(BUILD,{recursive:true});await fs.mkdir(OUT,{recursive:true});
await fs.writeFile(path.join(BUILD,'deck.json'),JSON.stringify(p.toProto(),null,2));
const candidate=path.join(BUILD,'candidate.pptx');
await (await PresentationFile.exportPptx(p)).save(candidate);
for (let i=0;i<p.slides.items.length;i++){
 const blob=await p.export({slide:p.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(BUILD,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await blob.arrayBuffer()));
}
const {finalizePresentation}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
const result=await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath:FINAL,pythonExecutable:PY,
 integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),
 explicitTotalSlideCount:8,requiredNativeTableOwnerSlides:[2,4,6,7],requiredNativeChartOwnerSlides:[],
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...([2,4,6,7].flatMap(x=>['--require-native-table-slide',String(x)]))],
 fontPolicy:{basis:'design',families:[F]},verifyArtifactToolImport:true,receiptPath:path.join(BUILD,'validation.json')});
console.log(JSON.stringify({file:FINAL,result}));

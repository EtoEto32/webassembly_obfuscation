"""Derive a compact, unit-labelled evidence index from saved research results."""
import argparse,hashlib,json,shutil,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];BASE=ROOT/'results/state-witness'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(out):
    out.mkdir(parents=True,exist_ok=False);sources={}
    def read(name):
        path=BASE/name;sources[name]=digest(path);return json.loads(path.read_text())
    basic=read('guard-import-direct-v1/manifest.json');pair=read('guard-import-direct-pair-v1/manifest.json');chain=read('guard-import-direct-chain-v2/results.json')
    costs=read('guard-import-direct-cost-v1/results.json');workers={m:[read('guard-import-direct-cost-v1/'+m+'-'+str(n)+'.json') for n in range(3)] for m in ('direct','smt')}
    timing={m:{'witnessBatchMedianSeconds':costs['summary'][m]['medianSeconds'],
        'preparationMedianSeconds':statistics.median(r['preparationSeconds'] for r in rows),
        'estimatedPreparationPlusBatchSeconds':statistics.median(r['preparationSeconds']+r['medianSeconds'] for r in rows)} for m,rows in workers.items()}
    worklist=[read('guard-import-worklist'+suffix+'/results.json') for suffix in ('-v1','-may-v1','-chain-v1')]
    replay=read('import-bundle-replay-v3/results.json');live=read('post-start-live-v1/results.json');coverage=read('coverage-v1/results.json')
    hashes={}
    for directory in ('guard-import-direct-v1','guard-import-direct-pair-v1','guard-import-direct-chain-v2'):
        for raw in (BASE/directory).glob('*.wasm'):hashes[raw.relative_to(BASE).as_posix()]=digest(raw)
    result={'scope':'Current K evidence index. Counts have different units and overlapping source programs; no aggregate bug count.',
        'direct':{'contracts':basic['contracts'],'initialStoreChecks':len(basic['signs']),'basicNegativeReplaysPerEngine':basic['runtimeComparisons'],
            'extraTwoImportReplaysPerEngine':pair['pairsPerEngine'],'longChainContracts':chain['contracts'],'longChainNegativeReplaysPerEngine':chain['negativeWitnesses'],
            'longestGeneratedApiSequence':chain['maxApiLength'],'distinctWasmHashesAcrossTheseThreeSources':len(set(hashes.values()))},
        'timing':{'methods':timing,'witnessOnlySmtOverDirect':timing['smt']['witnessBatchMedianSeconds']/timing['direct']['witnessBatchMedianSeconds'],
            'estimatedPreparationPlusBatchRatio':timing['smt']['estimatedPreparationPlusBatchSeconds']/timing['direct']['estimatedPreparationPlusBatchSeconds'],
            'notMeasuredEndToEnd':True,'authorToolComparison':False},
        'worklist':{'contracts':sum(r['contracts'] for r in worklist),'sameConditions':sum(r['statuses'].get('same-conditions',0) for r in worklist),'sharedWp':True},
        'artifact':{'status':replay['reproduction']['status'],'byteIdenticalFilesIncludingDuplicates':replay['reproduction']['byteIdenticalBinaries'],'sha256':replay['archiveSha256']},
        'ffmpegControl':{'completedWorkers':len(live['rows']),'failures':live['failures'],'originalApiCalls':sum(r['originalApiCalls'] for r in live['rows']),
            'probeCalls':sum(r['probeCalls'] for r in live['rows']),'lifetimeDifferencesPerEngine':next(r['live'] for r in live['rows'] if r['variant']=='retained'),
            'memoryBytesPerInstance':live['rows'][0]['memoryBytes'],'allMemoryHashesEqual':len({r['memoryBefore'] for r in live['rows']}|{r['memoryAfter'] for r in live['rows']})==1,
            'naturalRestoreBug':False,'videoWorkloadExecuted':False},
        'coverage':coverage['summary'],'sourceResultSha256':sources,'wasmSha256':hashes,
        'assessment':{'newGeneralAlgorithmEstablished':False,'naturalUseRequiringKEstablished':False,'researchPrototypeAndControlledEvidenceAvailable':True}}
    (out/'summary.json').write_text(json.dumps(result,indent=2))
    lines=['# 現在の実測の索引','', '2026-10-24。保存済みJSONから導出。契約・store・呼出し・binaryの件数を合算してbug件数にしない。','',
        '|項目|実測|意味|','|---|---:|---|',
        f"|直接生成の条件照合|{result['direct']['contracts']}契約 / {result['direct']['initialStoreChecks']} store|肯定側はこの追加検査では条件照合|",
        f"|小反例再生|{basic['runtimeComparisons']} + {pair['pairsPerEngine']} / engine|Node・Wasmtime。自然なbug件数ではない|",
        f"|長い反例|{chain['negativeWitnesses']} / engine、最大{chain['maxApiLength']} API|小反例の費用測定には混ぜない|",
        f"|既知worklist|{result['worklist']['sameConditions']}条件一致|parser・WPを共有|",
        f"|source-only artifact|{result['artifact']['byteIdenticalFilesIncludingDuplicates']} binary fileを再生成|複製を含む|",
        f"|ffmpeg制御変種|{result['ffmpegControl']['lifetimeDifferencesPerEngine']}寿命差 / engine|1 GiB hashは同じ、元API実行0|",'',
        f"反例生成部分の費用比は{result['timing']['witnessOnlySmtOverDirect']:.2f}倍。前処理と生成中央値の和の比は{result['timing']['estimatedPreparationPlusBatchRatio']:.2f}倍で、後者はend-to-endの正式測定ではない。",'',
        '新しい一般アルゴリズムと自然な必要例は未確立。[研究判断](../../../research/state-witness/status.md)・[草稿](../../../research/state-witness/paper-draft.md)・[再現手順](../../../research/state-witness/quickstart.md)を参照する。','']
    (out/'summary.md').write_text('\n'.join(lines),encoding='utf8');shutil.copy2(__file__,out/'overview.py')
    (out/'sha256.json').write_text(json.dumps({p.name:digest(p) for p in out.iterdir()},indent=2));print(json.dumps({k:result[k] for k in ('direct','worklist','artifact','ffmpegControl')}))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)

# -*- coding: utf-8 -*-
"""Preserve historical entries and add this experiment's evidence."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
marker='差分メモリ境界修復の追補（2026-10-19）'
note=('{marker}：[符号化したままのbulk copy]({link})を限定した実Wasm変換器へ実装。'
      '隣接byteのXOR差分、copy前の2区間補正、copy後の境界2点修復と区間共有を検査した。'
      '主・追加120 targetと各観測用版の計256,080呼出し、20,080 trapで値・状態の不一致0。'
      'WABT360 check、112,130小幅モデル比較、4誤変換反例、3拒否対照を保存。'
      '60主binaryのbyte再現も一致。45 fresh processで8KiB近接copyの全復号版約5067nsに対し境界版約39ns、'
      '遠いcopyの区間共有は約2429→1249nsと高速化した。しかし累積XORで変換48条件すべてを元binaryへ回復。'
      '公開profileの索引化により照合順の費用を除いても追加の保護効果は未確認。'
      '索引v1のdata-count照合不備は修正し耐性に数えない。'
      '差分・scan・符号化計算の先行性と具体規則の未確立な新規性を区別し、主発明には不採用。'
      '独自で有効な難読化・特許候補の確立は未達、goalはactive。')
names=['research/STATUS.md','research/literature-review.md','research/research-gap.md','research/candidates.md','research/threat-model.md','research/algorithm.md','research/novelty-analysis.md','research/experiments.md','research/patent/README.md','paper-draft.md']
for name in names:
    path=ROOT/name;text=path.read_text(encoding='utf-8')
    if marker in text:continue
    link='research/difference-boundary/README.md' if name=='paper-draft.md' else '../difference-boundary/README.md' if name.startswith('research/patent/') else 'difference-boundary/README.md'
    first,rest=text.split('\n',1)
    path.write_text(first+'\n\n'+note.format(marker=marker,link=link)+'\n'+rest,encoding='utf-8')
    print(name)

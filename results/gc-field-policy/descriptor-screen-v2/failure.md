# Nodeの実験feature版の不一致

Binaryen 133で5moduleのvalidationを通過したが、Node 24.15.0/V8 13.6はcustom-descriptors flagを有効にしてもlibrary function #0の`fb20`（struct.new_desc）をcompile拒否した。Node側実装と現在のproposal/Binaryen encodingの対応が揃っていない。実行した4caseの成功数は0。仕様からの予想と実engineの観測を区別する。

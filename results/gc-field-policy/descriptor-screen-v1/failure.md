# exact型の不足

Binaryen validatorがcopied-descriptorのconstructorを拒否。inexactな`ref.cast (ref T)`の結果から取り出したdescriptorはinexactであり、`struct.new_desc`が要求するexact descriptorではなかった。型付けが正しく拒否した例。v2で対象objectを`(ref (exact T))`へcastする。実行結果や防御成功には数えない。

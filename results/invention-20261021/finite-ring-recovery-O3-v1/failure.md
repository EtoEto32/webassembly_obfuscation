# 回復器の未対応による停止

O3が最高bit抽出のand1を除き、`i32.shr_u(param,31)`にした形を回復器がBoolean入力と認識しなかった。nonpolynomial gateとして停止。既知のunsignedシフトの範囲を認識する修正をv2で行う。旧scriptを保存した。この停止を解析耐性・時間切れ・意味保存違反に数えない。

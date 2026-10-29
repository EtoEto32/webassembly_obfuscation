# hash-wasm 4.12.0 適用範囲

|algorithm|operation|O3|analysis|state bytes|saved / full (35 calls)|reason|
|---|---|---|---|---:|---:|---|
|adler32|Hash_Init|false|ranges|4|140 / 140||
|adler32|Hash_Init|true|ranges|4|140 / 140||
|adler32|Hash_Update|false|full|4|140 / 140|unsupported value: i32.shr_u|
|adler32|Hash_Update|true|full|4|140 / 140|unsupported value: i32.shr_u|
|adler32|Hash_Final|false|full|4|140 / 140|unsupported value: i32.or|
|adler32|Hash_Final|true|full|4|140 / 140|unsupported value: i32.or|
|crc32|Hash_Init|false|full|4|140 / 140|unsupported statement: loop|
|crc32|Hash_Init|true|full|4|140 / 140|unsupported statement: loop|
|crc32|Hash_Update|false|full|4|140 / 140|unsupported value: i32.xor|
|crc32|Hash_Update|true|full|4|140 / 140|unsupported value: i32.xor|
|crc32|Hash_Final|false|full|4|140 / 140|unsupported value: i32.or|
|crc32|Hash_Final|true|full|4|140 / 140|unsupported value: i32.or|
|md5|Hash_Init|false|full|152|5320 / 5320|unsupported statement: i64.store|
|md5|Hash_Init|true|full|152|5320 / 5320|unsupported statement: i64.store|
|md5|Hash_Update|false|full|152|5320 / 5320|unsupported value: i32.shr_u|
|md5|Hash_Update|true|full|152|5320 / 5320|unsupported value: i32.shr_u|
|md5|Hash_Final|false|full|152|5320 / 5320|unknown store address|
|md5|Hash_Final|true|full|152|5320 / 5320|unknown store address|
|sha1|Hash_Init|false|full|92|3220 / 3220|unsupported statement: i64.store|
|sha1|Hash_Init|true|full|92|3220 / 3220|unsupported statement: i64.store|
|sha1|Hash_Update|false|full|92|3220 / 3220|unsupported value: i32.shl|
|sha1|Hash_Update|true|full|92|3220 / 3220|unsupported value: i32.shl|
|sha1|Hash_Final|false|full|92|3220 / 3220|unsupported statement: global.set|
|sha1|Hash_Final|true|full|92|3220 / 3220|unsupported statement: global.set|
|sha256|Hash_Init|false|full|112|3920 / 3920|unsupported statement: i64.store|
|sha256|Hash_Init|true|full|112|3920 / 3920|unsupported statement: i64.store|
|sha256|Hash_Update|false|full|112|3920 / 3920|only i32 params/locals and void functions supported|
|sha256|Hash_Update|true|full|112|3920 / 3920|only i32 params/locals and void functions supported|
|sha256|Hash_Final|false|full|112|3920 / 3920|only i32 params/locals and void functions supported|
|sha256|Hash_Final|true|full|112|3920 / 3920|only i32 params/locals and void functions supported|
|sha512|Hash_Init|false|full|208|7280 / 7280|unsupported statement: i64.store|
|sha512|Hash_Init|true|full|208|7280 / 7280|unsupported statement: i64.store|
|sha512|Hash_Update|false|full|208|7280 / 7280|only i32 params/locals and void functions supported|
|sha512|Hash_Update|true|full|208|7280 / 7280|only i32 params/locals and void functions supported|
|sha512|Hash_Final|false|full|208|7280 / 7280|only i32 params/locals and void functions supported|
|sha512|Hash_Final|true|full|208|7280 / 7280|only i32 params/locals and void functions supported|
|xxhash32|Hash_Init|false|full|48|1680 / 1680|unsupported statement: i64.store|
|xxhash32|Hash_Init|true|full|48|1680 / 1680|unsupported statement: i64.store|
|xxhash32|Hash_Update|false|full|48|1680 / 1680|unsupported statement: i64.store|
|xxhash32|Hash_Update|true|full|48|1680 / 1680|unsupported statement: i64.store|
|xxhash32|Hash_Final|false|full|48|1680 / 1680|only i32 params/locals and void functions supported|
|xxhash32|Hash_Final|true|full|48|1680 / 1680|only i32 params/locals and void functions supported|
|xxhash64|Hash_Init|false|full|80|2800 / 2800|only i32 params/locals and void functions supported|
|xxhash64|Hash_Init|true|full|80|2800 / 2800|only i32 params/locals and void functions supported|
|xxhash64|Hash_Update|false|full|80|2800 / 2800|only i32 params/locals and void functions supported|
|xxhash64|Hash_Update|true|full|80|2800 / 2800|only i32 params/locals and void functions supported|
|xxhash64|Hash_Final|false|full|80|2800 / 2800|only i32 params/locals and void functions supported|
|xxhash64|Hash_Final|true|full|80|2800 / 2800|only i32 params/locals and void functions supported|

既存save()はstateと4byteのbinary識別子を保持する。全memoryをコピーする対照とは区別する。上記は長寿命save()と同じAPIではない。
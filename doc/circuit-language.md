# 回路言語の仕様

回路ファイルの名前と型の検査、接続を定義する。受理する構文は[字句規則と回路文法](grammar.md)、評価と初期状態は[シミュレーション仕様](simulation.md)を参照する。

## コア言語

トップレベルは S 式とし、主要フォームは `using`、`func`、`module`、`struct`、`latch`、`memory`、`test` とする。回路本体で結線を定義するフォームは `def` とする。キーワードは英字を使い、引数の役割は `in`、`out` などの名前で示す。

```lisp
(using nor)
(func buffer (in x) (out x))

(func invert (in x) (out y)
  (def y (nor x x)))

(func half-adder (in x y) (out carry sum)
  (def carry (and x y))
  (def sum (xor x y)))

(func full-adder (in x y z) (out carry sum)
  (def (c1 s1) (half-adder x y))
  (def (c2 sum) (half-adder s1 z))
  (def carry (or c1 c2)))

(module sr-latch (in set reset) (out q nq)
  (def q (nor reset nq))
  (def nq (nor set q)))
```

設定の `sources` に載せる `logic.ncg2` のルート名前空間に、`and`、`xor`、`or` を NOR で定義する。信号値は0または1とし、固定値は定数配線として扱う。名前空間をまたぐ参照と回路の本体分割は[名前解決](names.md)に従う。

初版の `nor` は1ビット入力2本と1ビット出力1本を持つ。裸のポート名は `(bits 1)` の宣言と同じ型を持ち、`(in)` は入力を持たないことを表す。出力ポートは1本以上とし、入力列と出力列のそれぞれでポート名を一意とする。

`def` の左辺は単一名または出力名の列であり、右辺の結果とポート単位で対応させる。複数出力は順序を保って分解し、式の内部では単一出力を参照できる。幅は入力宣言と右辺の型から求め、出力宣言に対して検査する。入力名を出力に列挙する形は同一配線を公開する。例えば `buffer` はゲートを追加しない。入力以外の信号は一度だけ定義し、未定義名、多重駆動、幅・型・ポート数の不一致はコンパイルエラーとする。

`func` は定義済みの信号のみ参照し、基底ゲートと他の `func` を使う組み合わせ回路である。`module` は内部信号を前方参照でき、ラッチ、RAM、他のモジュール、ワイヤのフィードバックを記述できる。モジュールの局所信号は全 `def` から先に収集し、ポート宣言と式から型を決める。型は一意に決まり、ビット幅は正でなければならない。配線参照だけで閉じる循環は拒否し、フィードバックはゲートまたは状態素子を経由する。呼び出し先の定義はファイル内の掲載位置に依存せず解決し、展開段階で回路定義間の再帰を拒否する。

### ビット列と struct

| 構文 | 意味 |
| --- | --- |
| `(in x (a (bits 32)))` | 1ビットの `x` と32ビットの `a` を入力にする。出力も同じ形式で宣言する |
| `(bit a 5)` | インデックス5の1ビット |
| `(slice a 4 8)` | インデックス4から11までの8ビット |
| `(slice a 0 4 2)` | インデックス0、2、4、6の4ビット。`slice` の引数は開始、選択数、任意の正の刻み |
| `(concat lo hi)` | 引数順に連接し、`lo` を低インデックス側に置く |
| `(field inst rs1)` | `inst` の型が定義する `rs1` フィールドを参照する |
| `(as Inst32 bus)` / `(raw inst)` | 同じ総ビット幅のビット列と struct の間で表現を変換する |

ビット幅と `slice` の選択数は正とする。開始位置は0以上で、選択する全インデックスがビット列の範囲に入ることを静的に検査する。`bits` ではインデックス0が最下位ビットとなる。ポートへの暗黙の連接、拡張、切り詰めはエラーとし、連接が必要な場合は `concat` を記す。ビット列リテラル `#b0011` や `#x03` は、期待幅があればその幅で表せる非負の値として読む。期待幅がなければ二進の1桁を1ビット、十六進の1桁を4ビットとして幅を決める。

```lisp
(struct Inst32 (width 32)
  (opcode (bits 7) (at 0))
  (rd     (bits 5) (at 7))
  (funct3 (bits 3) (at 12))
  (rs1    (bits 5) (at 15))
  (rs2    (bits 5) (at 20))
  (funct7 (bits 7) (at 25)))

(func decode (in (inst Inst32)) (out (rs1 (bits 5)) (op-low (bits 2)))
  (def rs1 (field inst rs1))
  (def op-low (slice (field inst opcode) 0 2)))
```

`at` はビットオフセットを表す。フィールド名の重複、範囲外、重なりを拒否する。空きビットは `raw` と `as` の往復で保存し、フィールド経由では参照しない。宣言を基準に型の同一性を判定し、同じ幅の別レイアウトへの解釈には `raw` と `as` を使う。構造体のレイアウトはワイヤの配置を指定する。フィールドが別の `struct` を参照するときは、参照先の総ビット幅で範囲と重複を検査する。フィールド型の参照グラフに循環がある場合は型エラーとする。

旧版の `a(32)` は `(a (bits 32))`、`a[0,15]` は `(slice a 0 16)`、`a[0,31,2]` は `(slice a 0 16 2)` に移行できる。旧版の開区間と半開区間も、実際に選択する最初のビットと選択数に変換する。空の選択は配線から除き、必要であればポート宣言を見直す。旧出力ポートにスライスがあれば、対応する信号を `def` で公開する。

## 状態素子の構文

```lisp
(latch pc-store (width 32))
(memory work-ram (address 16) (data (bits 32)))

(module pc-unit (in (next-pc (bits 32)) enable) (out (pc (bits 32)))
  (def pc (pc-store next-pc enable)))

(module ram-unit
  (in (address (bits 16)) (data (bits 32)) write-enable)
  (out (data-out (bits 32)))
  (def data-out (work-ram address data write-enable)))
```

ラッチと RAM の値の更新は[状態素子の規則](simulation.md#状態素子)に従う。

## 定常化と周期の注釈

定常化の上界は[静的解析](static-analysis.md#自動解析)で推定できる。ソースへの記述は任意であり、設計上の期待値を残す場合は、サブモジュールを含めそのモジュール自身の入力ポートについて条件を宣言する。

契約注釈の構文案では、`module` 本体の先頭に `(settles-within N)` または `(periodic-within N p)` を1つ記す。$`N`$ は0以上、$`p`$ は正の整数で、`settles-within` は $`p=1`$ を指定する。[状態の繰り返し](simulation.md#定常状態と周期定常状態)と[条件の検査](static-analysis.md#指定した条件の検査)を参照する。

```lisp
(module two-stage (in x) (out y)
  (def a (nor x x))
  (def y (nor a a)))

(module oscillator (in) (out q)
  (periodic-within 0 2)
  (def q (nor q q)))
```

`two-stage` は注釈を持たない。固定入力を適用して2 tick以内に全ゲートが定常になることをゲートの深さから推定できる。`oscillator` は構文案の注釈を使った例であり、毎 tick 反転する `q` が2 tickごとに戻ることを要求している。この回路では1 tick で必ず値が変わるため、基本周期も2である。

## 回路テスト

```lisp
(test full-adder
  (case (in 1 1 1) (expect 1 1))
  (case (in 0 1 1) (expect 1 0)))

(test sr-latch
  (reset)
  (drive 1 0)
  (tick 1)
  (expect 1 0)
  (drive 0 1)
  (tick 1)
  (expect 0 0)
  (tick 1)
  (expect 0 1)
  (drive 0 0)
  (tick 3)
  (expect any 1))
```

`case` は `func` を各入力で独立に評価する。`module` のテストは初期状態から開始し、`reset` で再初期化できる。`drive` は次の tick に適用する全入力を設定し、次の `drive` まで保持する。`expect` は最後に確定した出力を読む。`any` は対応する出力ポート全体を比較から除く。各入力列と期待値列は対象のポートの宣言順に対応し、ポートごとに値を一つ指定する。ビット列ポートには幅に収まるリテラルを使う。1ビットポートでは `0` と `1` も使える。`struct` 型のポートには `(as 型 リテラル)` を使い、指定型がポート型と一致することを検査する。リテラルはその型の総ビット幅で解釈する。比較は空きビットを含めた全ビットを対象とする。

```lisp
(test decode
  (case (in (as Inst32 #x000a0003)) (expect #b10100 #b11)))
```

失敗時はテスト対象の完全修飾名、テストブロックの位置、ケース番号または tick、該当する出力、期待値と実測値を返す。

生成テストについては[関数型言語の仕様](macros.md#展開結果の保証とテスト)を参照する。

## 参照資料

- 現行 circuitgame の [構文例](https://github.com/neknaj/circuitgame/blob/3359eff0b5e852f0321a3f101799bf5db2ddb57f/spec/sample.ncg)、[パーサー](https://github.com/neknaj/circuitgame/blob/3359eff0b5e852f0321a3f101799bf5db2ddb57f/src/rust/compiler/parser.rs)、[VM](https://github.com/neknaj/circuitgame/blob/3359eff0b5e852f0321a3f101799bf5db2ddb57f/src/rust/vm/mod.rs)、[テスト実行](https://github.com/neknaj/circuitgame/blob/3359eff0b5e852f0321a3f101799bf5db2ddb57f/src/rust/test/test.rs)

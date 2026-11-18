# 初版の字句規則と回路文法

## 字句

ソースの文字コードは UTF-8 とする。空白は ASCII のスペース、タブ、LF、CR を使う。文字列の外にある `;` から改行または入力末尾までを行コメントとする。括弧、空白、コメント、入力末尾をトークンの境界とする。文字列の開始・終了は二重引用符で指示する。隣り合うアトムの間には空白またはコメントを置く。

| トークン | 規則 |
| --- | --- |
| 名前 | ASCII の英字または `_` で始まり、以降は ASCII の英数字、`_`、`-` を使える。大文字と小文字を区別する |
| 自然数 | ASCII の十進数字1桁以上。先頭の0を許す。字句上の値を自然数として読み、用途ごとの範囲検査を行う |
| 負の整数 | `-` に十進数字を続ける。共通の字句解析で認識し、関数型言語で整数として使う |
| ビット列 | `#b` に二進数字、または `#x` に十六進数字を1桁以上続ける。十六進数字の英字は大小両方を許す |
| 文字列 | 二重引用符で囲む。内部で許すエスケープは `\"` と `\\`。引用符とバックスラッシュはエスケープし、改行は字句エラーとする |

アトムはトークン全体で分類する。例えば `12foo` と `#b102` は不正なトークンである。予約語は文法上の位置で認識する。例えば `reset` はテストの操作名にも、回路の入力ポート名にもなれる。`0` と `1` は自然数トークンであり、値の位置では1ビット定数になる。

## S 式と回路フォーム

以下は EBNF である。引用符で括った記号はトークン、波括弧は0回以上の繰り返し、角括弧は省略可能を示す。`name`、`nat`、`string`、`bit-literal` は前節のトークンである。S 式の層はアトムとリストの木を作り、回路フォームの層でリストの用途と要素数を確認する。

```ebnf
sexpr       = atom | "(" { sexpr } ")" .
root        = "(" "using" "nor" ")" { declaration } .
included    = { declaration } .
declaration = "(" "include" string ")" | routine | structure
            | latch | memory | test .
routine     = "(" ( "func" | "module" ) name inputs outputs { definition } ")" .
inputs      = "(" "in" { port } ")" .
outputs     = "(" "out" { port } ")" .
port        = name | "(" name type ")" .
type        = name | "(" "bits" nat ")" .
definition  = "(" "def" targets expr ")" .
targets     = name | "(" name { name } ")" .
expr        = name | value | call
            | "(" "bit" expr nat ")"
            | "(" "slice" expr nat nat [ nat ] ")"
            | "(" "concat" expr { expr } ")"
            | "(" "field" expr name ")"
            | "(" "as" name expr ")" | "(" "raw" expr ")" .
call        = "(" callee { expr } ")" .
value       = "0" | "1" | bit-literal .
structure   = "(" "struct" name "(" "width" nat ")" { field } ")" .
field       = "(" name type "(" "at" nat ")" ")" .
latch       = "(" "latch" name "(" "width" nat ")" ")" .
memory      = "(" "memory" name "(" "address" nat ")" "(" "data" type ")" ")" .
test        = "(" "test" name ( case { case } | action { action } ) ")" .
case        = "(" "case" "(" "in" { value } ")" "(" "expect" { expected } ")" ")" .
action      = "(" "reset" ")" | "(" "drive" { value } ")"
            | "(" "tick" nat ")" | "(" "expect" { expected } ")" .
expected    = value | "any" .
```

`atom` は名前、自然数、負の整数、ビット列または文字列である。`callee` は名前のうち、式の専用フォームである `bit`、`slice`、`concat`、`field`、`as`、`raw` を除いたものとする。型・値の範囲、式の単一出力、呼び出しの引数とポートの一致は[回路言語の意味規則](circuit-language.md#コア言語)で検査する。

ルートは `(using nor)` を先頭に1回記す。インクルード先は宣言の断片であり、基底の宣言をルートと共有する。インクルードは記述元のディレクトリを基準とする仮想相対パスとして解決する。同一の正規化済みパスは一度だけ読む。読み込み中のパスを再び含む場合は循環として報告する。この文書でルートと明記しない回路例は、宣言の断片として掲載できる。

`case` の列は `func`、操作の列は `module` に対して使う。`tick 0` は状態を進めず、設定済みの入力も適用しない。`any` は出力ポート1本分の比較を省略する。

厳格パーサーは入力末尾まで読み、字句・S 式・フォームのいずれかに誤りがあれば拒否する。[回復パーサー](diagnostics.md#エラー回復)も同じ字句規則とフォームを使う。マクロと定常化の契約注釈は拡張として別に扱う。

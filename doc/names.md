# ソース集合と名前解決

回路記述と純粋関数型言語は、ソースの選択、名前空間、公開、別名の規則を共有する。

## ソース集合

プロジェクトのソース集合は [設定の `sources`](project-config.md) で決まる。ホストはこの集合の UTF-8 スナップショットを core に渡す。単独ファイルの解析では、指定したファイルを解析する。単独で実行する回路は `.ncg2` に書く。

core はスナップショットの仮想パスの拡張子を大文字・小文字を区別して照合し、`.ncg2` を回路ソース、`.ncg2m` を関数型ソースとして解析する。設定に列挙できる拡張子はこの2種類とする。

各ファイルの識別子はプロジェクトルートからの正規化済み仮想相対パスとする。区切りは `/` とし、大文字と小文字を区別する。正規化で `.` と打ち消せる `..` を除去し、ルート外に出るパス、絶対パス、空のパスを拒否する。同じ識別子は一度だけ読む。異なる識別子は、内容やホスト上の実体が同じでも別ソースとして扱う。依存パッケージの読み込みは将来の拡張とし、完全修飾名のルートはここで選んだプロジェクトを指す。

## 名前空間と公開

```lisp
(namespace logic
  (export invert)
  (func invert (in x) (out y)
    (def y (nor x x))))
```

`(namespace logic ...)` は `::logic` に、`(namespace logic::internal ...)` は `::logic::internal` に宣言を加える。ひとつのファイルに複数の名前空間ブロックを書ける。同じパスを指定した全ブロックは、ファイルと言語をまたいで同じ宣言表を共有する。ブロックの外に書いた宣言はルートに属する。名前空間ブロックはファイルのトップレベルに並べる。名前空間は入出力を持つ回路の `module` と独立している。

初版では、同じ名前空間で宣言名（回路、型、補助関数、マクロなど）と直下の名前空間名を一意とする。同じ名前の独立した宣言は内容にかかわらず重複エラーとする。名前空間はパスの中間要素にも作られる。テストが対象を指す名前は宣言名の追加とは扱わない。

`(export name ...)` は現在の名前空間に属する宣言を公開する。公開対象は別ファイルの同じ名前空間で定義してもよい。複数の指定が同じ宣言を公開する場合は一件として扱う。非公開の宣言は同じ名前空間から参照できる。公開の判定は末端の宣言に対して行い、途中の名前空間は修飾に使える。設定ファイルの `entry` はプロジェクト内の構成として完全修飾名で回路を選択できる。

## 完全修飾名と use

`::logic::invert` の先頭の `::` はプロジェクトルートを表す。完全修飾名の探索は宣言表だけを使う。同じ名前空間の宣言と他の名前空間の公開宣言を、`use` なしで参照できる。

```lisp
(namespace app
  (use ::logic::invert inv)
  (use ::logic gates)
  (module main (in x) (out a b c)
    (def a (::logic::invert x))
    (def b (inv x))
    (def c (gates::invert x))))
```

`(use 完全修飾名 別名)` は宣言または名前空間を指す別名を作る。別名の有効範囲はその名前空間ブロック全体であり、同じ名前空間の別ブロックには伝わらない。ブロック外の `use` は同じファイルのブロック外に限って有効とする。別名の参照先は完全修飾名で指定し、他の別名に依存しない。名前空間の別名に続くパスは、元の名前空間のパスから解決する。別名を経由しても、公開範囲と使用位置の宣言種別・実行段階の制約を検査する。別名の再公開と一括取り込みは初版の文法に含めない。

無修飾の宣言参照は同じ名前空間の宣言と現在のブロックの別名を対象とする。該当する束縛がなければ、その位置と実行段階で使える組み込みを探す。構文専用フォームは各言語の文法で判定する。回路の局所信号と関数の局所変数は既存の字句スコープで解決する。例えば `inv` という回路の入力線を信号式で参照しても、呼び出し位置の `(inv x)` は回路の別名を参照する。

先頭に `::` がない複数要素のパスは、現在の名前空間の直下にある名前空間、またはそのスコープの名前空間の別名からたどる。例えば `logic` 内の `internal::helper` は `::logic::internal::helper` を指す。参照先の公開範囲はどちらの表記でも同じである。

## 同一性と衝突

宣言の同一性は宣言表で決まる。完全修飾名、宣言の別名、名前空間の別名を経由した参照は、解決した元の宣言を共有する。異なる名前で同じ回路定義を参照しても、呼び出しごとの回路インスタンスの割り当ては通常の呼び出しに従う。

`use` 同士の比較範囲は同じ別名スコープとする。別名と宣言・子名前空間の比較には、現在の名前空間に属する全ブロックの宣言表を使う。

| 状況 | 判定 |
| --- | --- |
| 複数の `use` が同じ別名で同じ宣言または名前空間を指す | 一つの束縛として受理し、最初の指定を除く各 `use` に重複警告を出す |
| 異なる別名が同じ宣言または名前空間を指す | 両方を受理する |
| 同じ別名が異なる対象を指す | 衝突。指示と対象の位置を示す |
| 別名と同じ名前の直接の宣言または子名前空間がある | 同じ対象なら一つの束縛。異なる対象なら衝突 |
| 独立した宣言が同じ完全修飾名を定義する | 重複定義。各宣言の位置を示す |

## 回路の本体分割

`(module-part name (def ...) ...)` は同じ名前空間にある `module` に結線を加える。ポートと局所信号を共有し、各断片の宣言参照にはその断片の別名スコープを使う。`module` はポートを宣言する。`module-part` の対象はその `module` の無修飾名とする。対象が未定義、または別の宣言種別の場合は診断する。マクロを展開し、全断片から局所信号を集めた上で、型、未定義名、多重駆動を検査する。

## 複数ファイルのプロジェクト例

`circuitgame2.toml`

```toml
sources = ["main.ncg2", "output.ncg2", "logic.ncg2m"]
entry = "::app::main"
```

`main.ncg2`

```lisp
(using nor)

(namespace app
  (use ::logic::emit-invert invert)
  (module main (in x) (out y)
    (expand invert mid x)))
```

`output.ncg2`

```lisp
(namespace logic
  (export buffer)
  (func buffer (in x) (out x)))

(namespace app
  (module-part main
    (def y (::logic::buffer mid))))
```

`logic.ncg2m`

```lisp
(namespace logic
  (export emit-invert)

  (defn invert-expression
    (as-type (Fn (Syntax) Syntax)
      (fn (x) (syntax (nor (unsyntax x) (unsyntax x))))))

  (defmacro emit-invert (out x)
    (list (syntax (def (unsyntax out) (unsyntax (invert-expression x)))))))
```

`::logic` は回路の `buffer` とマクロの `emit-invert` を公開する。補助関数 `invert-expression` の署名は構文を1個受け取り、構文を1個返すことを表す。`main.ncg2` のマクロ展開が生成した `mid` を `output.ncg2` の断片が参照する。入力 `x` を適用した tick の確定時に、その反転が出力 `y` に現れる。

## 検証する性質

- 完全修飾名の解決結果は `use` の有無や順序に依存しない。受理された別名での参照は、対応する完全修飾名での参照と同じ宣言を指す。
- ソース集合と各宣言が同じであれば、ファイル列の並び替えと同一ファイルの重複列挙によって宣言の同一性と衝突の有無は変わらない。
- 宣言の名前空間、公開、参照位置の別名環境を保ってファイルを分割しても、各参照は同じ宣言を指す。マクロ展開では定義側と挿入断片の束縛を保持する。

## 参照資料

- [The Rust Reference の Use declarations](https://doc.rust-lang.org/reference/items/use-declarations.html)
- [C# 言語仕様の Namespaces](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/language-specification/namespaces)
- [Common Lisp HyperSpec の Prevention of Name Conflicts](https://www.lispworks.com/documentation/HyperSpec/Body/11_aabe.htm)

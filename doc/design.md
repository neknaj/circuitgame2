# circuitgame2 設計

## 方針

circuitgame2 は、論理回路の接続と離散時間での動作を記述し、同じ回路を CLI と Web で実行する。通常の論理は2入力 NOR に展開する。ラッチと RAM は、専用宣言に対応する状態素子として VM 内の配列で扱う。ストレージとフラッシュメモリはホスト側の I/O デバイスとする。対象とする時間はシミュレーションの tick であり、配線遅延や電気特性はモデルの範囲外とする。

## リポジトリと依存関係

| リポジトリ | 責務 |
| --- | --- |
| [circuitgame2](https://github.com/neknaj/circuitgame2) | `doc/` の仕様、共通サンプル、期待する出力・trace、リリースの組み合わせを検査する CI |
| [circuitgame2-core](https://github.com/neknaj/circuitgame2-core) | Rust の構文解析、型・結線検査、ネットリスト、VM、テスト実行、エディタ向け言語サービス、後から加える Lisp、Verus の仕様と証明 |
| [circuitgame2-web](https://github.com/neknaj/circuitgame2-web) | WASM バインディング、エディタ、可視化、ブラウザの入出力と永続化 |
| [circuitgame2-cli](https://github.com/neknaj/circuitgame2-cli) | Rust のコマンド、診断表示、ファイル入出力、ネイティブと WASI の実行環境、LSP サーバーの通信・プロトコル変換 |
| `circuitgame2-editors`（作成予定） | Neovim と VS Code の拡張、エディタ別のパッケージ作成、LSP サーバーとの互換性テスト |

Web と CLI は core に直接依存する。メインの統合 CI は各リポジトリのコミットを指定してチェックアウトし、共通サンプルを検査する。core 内のライブラリや証明は必要に応じて Cargo workspace 内のクレートに分ける。メイン、core、web、CLI に editors を加えた5リポジトリで構成する。editors は CLI が配布する `circuitgame2-lsp` を LSP 経由で利用する。エディタ固有の設定や配布を変更したときは、editors から対象の拡張だけを更新できる。

配布時は Cargo の git 依存を使用する。core を参照する下流は同一 URL と同一の40桁コミット ID を `rev` に使い、対応する `version` も記す。Cargo は取得先のコミットを `rev` で選び、そのコミットのパッケージが `version` の要件を満たすか検査する。各配布側の `Cargo.lock` をコミットし、CI は `--locked`、`cargo tree -d`、lockfile の core の取得元とコミット ID、およびメインで指定したコミットの一致を確認する。

リリースでは core にタグを付けて指すコミット ID を確定し、Web と CLI の依存宣言と lockfile をそれぞれ更新する。その2つのコミットをメインの専用更新 PR で指定し、まとめて検査する。ローカル開発では checkout を並べ、Cargo の実行ルートに適用される外部設定で `[patch."https://github.com/neknaj/circuitgame2-core"]` に path を指定する。patch 先も `version` 要件を満たす必要がある。ローカル設定と patch に伴う一時的な lockfile の差分は配布から除外する。公開 registry への移行は各クレートを公開できる状態になった時点で判断する。

## コア言語

トップレベルは S 式とし、主要フォームは `using`、`include`、`func`、`module`、`struct`、`latch`、`memory`、`test` とする。回路本体で結線を定義するフォームは `def` とする。キーワードは英字を使い、引数の役割は `in`、`out` などの名前で示す。

```lisp
(using nor)
(include "logic.cg2")

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

`logic.cg2` には `and`、`xor`、`or` を NOR により定義する。`(using nor)` はルートファイルに置き、インクルード先と基底を共有する。初期の実装は旧版に合わせて NOR を実装する。NAND を加える場合も、1つの回路は宣言で選んだ基底に展開する。信号値は0または1とし、固定値は定数配線として扱う。インクルードは仮想パスで解決し、呼び出し元が UTF-8 のソースを供給する。循環と同名定義は診断する。

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

ビット幅と `slice` の選択数は正とする。開始位置は0以上で、選択する全インデックスがビット列の範囲に入ることを静的に検査する。`bits` ではインデックス0が最下位ビットとなる。ポートへの暗黙の連接、拡張、切り詰めはエラーとし、連接が必要な場合は `concat` を記す。`(bits 8)` などの期待型がある位置では `#b0011` や `#x03` を非負の値として読んでゼロ拡張する。期待型がない位置では二進の桁数または十六進の桁数の4倍を幅とし、期待幅で表せない値を拒否する。

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

`at` はビットオフセットを表す。フィールド名の重複、範囲外、重なりを拒否する。空きビットは `raw` と `as` の往復で保存し、フィールド経由では参照しない。型名でレイアウトを識別し、同じ幅の別レイアウトへの解釈には `raw` と `as` を使う。構造体のレイアウトはワイヤの配置を指定し、ホストの Rust 型の ABI やバイト順には依存しない。

旧版の `a(32)` は `(a (bits 32))`、`a[0,15]` は `(slice a 0 16)`、`a[0,31,2]` は `(slice a 0 16 2)` に移行できる。旧版の開区間と半開区間も、実際に選択する最初のビットと選択数に変換する。空の選択は配線から除き、必要であればポート宣言を見直す。旧出力ポートにスライスがあれば、対応する信号を `def` で公開する。

## tick と状態素子

`func` 単体の評価は入力に対する組み合わせ結果を返す。`module` 内で使った `func` は基底ゲートに展開され、各ゲートを他のゲートと同じ規則で進める。したがってゲート深さは `module` 内の出力 trace に反映される。配線の参照、スライス、連接、フィールド参照には tick を消費しない。

tick の開始時に入力フレームを適用する。すべてのゲートと状態素子はその入力と更新前の内部状態を読み、tick の終了時に結果を同時に確定する。定義を並べ替えても結果は同じである。ゲートが出した新しい値を別のゲートや状態素子が使用できるのは次の tick からとなる。reset 直後は tick 0 とし、入力とゲート出力を0、状態素子を初期値に戻す。初期値の既定は0で、ホストは reset と別に新しい入力フレームを与えられる。

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

| 状態素子 | tick の動作 |
| --- | --- |
| `latch` | enable が1なら当該 tick の入力値を保持部に取り込み、tick 終了時に出力する。0なら保持する |
| `memory` | 各 tick でアドレスから1語読み出し、tick 終了時に出力する。書き込み許可が1なら同じアドレスに書く。その tick の読み出しには更新前の値を返す |

`memory` は1つのアドレスを読み書きで共有し、`address` 幅を A とすると $2^A$ 語を持つ。例の RAM は64 Ki語、256 KiBである。呼び出し箇所ごとに独立した素子を割り当てる。アドレス空間と割当サイズは検査付き演算で計算し、設定した容量上限を超えた時点で診断する。アドレスの変換や語の移送にはそれぞれ幅に応じた処理が要る。ホスト配列は状態素子の意味論を直接実装する。任意のゲートで組んだラッチを配列へ自動置換できる条件は別途検証する。

旧版は通常のネットリストを順に処理し、処理済みのゲート出力を同じ周回で参照する。旧版のテスト行は同じ VM 上で順に1周ずつ進む。新方式では、SR ラッチの `(q nq)` が `(1 0)` のときに `(set reset)` を `(0 1)` に固定すると、`(0 0)`、`(0 1)` と2 tick かけて遷移する。旧版の順序では1周で `(0 1)` になる。旧テストの期待値は、外部から観測する時刻を明示して移行する。

## テストと Lisp

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

`case` は `func` を各入力で独立に評価する。`module` のテストは初期状態から開始し、`reset` で再初期化できる。`drive` は次の tick に適用する全入力を設定し、次の `drive` まで保持する。`expect` は最後に確定した出力を読む。`any` は対応する出力ポート全体を比較から除く。失敗時はテスト名、tick、対応する出力、期待値と実測値を返す。

初期実装では上記の固定ケースと時系列テストを提供する。次の段階で純粋関数型の評価器を導入する。マクロは構文オブジェクトを受け取り、束縛と位置情報を保った `def` の列を生成する。生成結果も通常の型・結線検査に通す。テスト用の関数には、コンパイル済みの回路と入力列から出力 trace を返す機能を提供する。マクロ、外付けインターフェイス、テストは評価器を共有し、組み込み関数は用途ごとに定める。停止性と一時停止・再開の規則は[関数型言語の設計](macros.md)に記す。

## 外部 I/O と可視化

回路は入力・出力ポートを通してホストとデータを交換する。ストレージとフラッシュメモリは、そのポートへ接続する外部デバイスである。CLI はファイル、Web はブラウザ側の永続化を担当する。要求は回路の出力、応答はホストの入力フレームで伝える。デバイス設定で要求と応答の幅、エラー応答、論理 tick 単位の遅延、電源投入・reset 時の扱いを定める。転送は tick の開始時に、前回確定した回路出力と今回の入力フレームの `valid` と `ready` を照合し、双方が1のときに成立する。受理した要求への応答は最短で次の tick の入力になる。初期のデバイスは同時に1件の要求を扱い、相手が受理できるまで転送内容を保持する。永続データは回路の reset と独立に扱い、フラッシュの消去・書き込み制約はそのデバイスに属する。テストでは決定的な応答列、または同じポート契約のメモリ上のデバイスを使用する。ホストで処理が終わるまで待つ場合は、指定した論理 tick の入力を確定できる時点まで VM を停止する。

可視化の設定は Web 側に置く。スイッチは次の入力フレームを編集し、LED と波形は確定後のポート値を読む。画面表示では、指定された VRAM インスタンスの確定済みの内容を読み取り専用で取得し、ホスト側の表示形式を適用する。画面から回路へ値を与える操作も入力ポートを通す。旧 `graphical` の座標とピンの対応は、小規模回路向けの Web 側設定で表現できる。初期の Web はスイッチ、LED、tick 操作から実装し、波形と VRAM 表示を後から追加する。

ユーザーは[外付けインターフェイス](macros.md#外付けインターフェイス)を純粋関数型言語で記述できる。インターフェイスは自身の状態、確定済みの回路出力、ホストイベントを受け取り、次の状態と回路入力、ホストへの要求を返す。要求は当該 tick の確定時にホストへ渡す。

## 言語サービスと LSP

言語サービスの実装は `no_std + alloc` の core に置き、Verus で検証する。コンパイラと同じ構文解析、名前解決、幅・型・結線検査から診断、定義への移動、参照検索、ホバー、補完候補、セマンティックトークンを求める。未完成のソースも解析し、診断と確定できた結果を返す。解析対象は文書 ID、文書バージョン、UTF-8 テキストからなるスナップショットとし、インクルード先はホストが渡す。問い合わせはそのスナップショット上のバイト範囲を扱う。Verus ではまず、範囲の両端が対象文書内の UTF-8 文字境界にあること、正規化した有効位置が往復変換で保存されること、解決済みシンボルが有効な定義を指すことを証明する。問い合わせを追加するたびに、共通の解析結果を使って対応する事前条件と事後条件を記述する。

CLI リポジトリには `circuitgame2-lsp` を別バイナリとして置く。標準入出力の JSON-RPC、LSP メッセージと core 型の対応、ファイル URI、セッションと要求の取り消しを担当する。LSP の位置エンコーディングはクライアントと交渉し、指定がない場合は UTF-16 を使う。文字・行位置と UTF-8 byte offset の変換は core の純粋関数を呼び出す。Web エディタは同じ問い合わせを WASM 経由で使う。LSP/JSON-RPC の型は core の公開 API に含めない。

### Neovim と VS Code の拡張

両エディタで `.cg2` を言語 ID `circuitgame2` として登録する。拡張は括弧の対応、コメント操作、基本的な色付けを提供し、同じ `circuitgame2-lsp` に接続する。診断、補完、ホバー、定義への移動は LSP の標準機能で提供する。基本の色付けは起動前から使え、サーバーがセマンティックトークンを提供したときは、入力ポートや回路名などを解析結果に基づいて色分けする。回路の構文解析や型情報の計算は core が担当する。

| エディタ | editors リポジトリ内の配置 | 実装 |
| --- | --- | --- |
| Neovim 0.11 以降 | `nvim/` | Lua でファイル種別と LSP 設定を登録する。`ftplugin/` にインデントやコメントの設定、`syntax/` に基本の色付け、`lsp/circuitgame2.lua` にサーバー設定を置く。Neovim 組み込みの LSP クライアントを `vim.lsp.enable("circuitgame2")` で有効にする |
| VS Code デスクトップ | `vscode/` | `package.json` の言語宣言、言語設定、TextMate grammar、TypeScript の `vscode-languageclient` で構成する。`.cg2` を開いたときに有効になり、サーバーをワークスペース側の拡張ホストで起動する |

初回は開いているファイルと、そこから `include` をたどって到達するファイルを解析する。プロジェクトのルートは最寄りの `circuitgame2.toml` のあるディレクトリを優先し、それがなければ Git リポジトリのルート、それもなければファイルの親ディレクトリとする。両エディタで単独ファイルも解析できる。相対 `include` は記述したファイルのディレクトリを基準に解決し、未保存の変更がエディタから届いていればディスク上の内容より優先する。

初回は CLI リリースにサーバーを含め、両拡張から `PATH` 上の `circuitgame2-lsp` を起動する。editors は Neovim 向けに `nvim/` をルートとするアーカイブを配布し、VS Code 向けに `.vsix` を配布する。Neovim ではアーカイブの展開先を `runtimepath` に登録する。実行ファイルのパスを指定する場合、Neovim はユーザーの LSP 設定、VS Code は実行ホストのマシン設定を使う。VS Code Remote では WSL、SSH 先、またはコンテナ側にサーバーを用意する。各拡張が対応するサーバーバージョンを公開し、editors の CI で対象の CLI リリースとの組み合わせを検査する。対応 OS・CPU のビルドが揃った段階で、CLI リリースのタグと配布ファイルのチェックサムを固定し、対象別のサーバーを同梱した VSIX を生成する。

受け入れテストでは両エディタで共通のサンプルを開き、単独ファイル、複数ファイルの `include`、未保存編集、日本語や絵文字を含む行で診断と定義位置が一致することを検査する。Neovim は headless で、VS Code は拡張のテストホストで起動する。サーバーを起動できない環境では基本の色付けが動作し、起動に必要な情報をユーザーへ表示する。

## Rust 実装と検査

core は `#![no_std]` と `alloc` を使用する。構文木、診断、ネットリスト、VM 状態は動的な容量を使い、実行環境がアロケータを提供する。構文解析とロード、VM の状態遷移とホスト I/O はそれぞれ別の API とする。core は UTF-8 の入力、型で検査した回路、入力フレームを受け取り、診断と状態遷移の結果を返す。エラー種別は `enum`、ソース位置は span で表し、文面と表示は CLI と Web が担当する。OS 依存のファイル、時計、乱数、Canvas API はアダプターに置く。Web では VM 状態を WASM 側に保持し、描画はコピーした観測値から作る。

Verus はパーサー、コンパイラ、VM、言語サービス、マクロ評価器の実行コードに適用する。文法に従う入力の受理、型・結線検査の健全性、ネットリストへの変換による意味保存など、利用者が依存できる契約を証明する。`func` の単体評価では出力値の一致を、`module` では tick ごとの観測結果の一致を示す。対象とする性質、証明の前提、CI での確認方法は[検証設計](verification.md)に記す。Verus と Rust のバージョンを固定し、`cargo verus verify` と通常の Cargo ビルドで同じ core を使う。`vstd` の機能設定、`no_std + alloc`、ブラウザ向け `wasm32-unknown-unknown` のビルドを小さな実装で確認してから依存を確定する。

| 段階 | 完了条件 |
| --- | --- |
| 1. 構文と組み合わせ評価 | NOR、`func`、`def`、複数出力、ビット幅、スライス、struct を実装する。パーサーの文法適合と型・結線検査、ネットリストへの変換による出力値の保存を Verus で検証する。ネイティブと WASM で同じ core をビルドできる |
| 2. 順序回路と RAM | SR ラッチ、発振器、RAM の同アドレス読み書き、初期化、インスタンス分離を trace で検査する。初期状態と1 tick の対応から、ソースとネットリストの観測結果の一致を Verus で示す |
| 3. CLI・Web・LSP・統合 | ネイティブ CLI、WASI CLI（`wasm32-wasip2`）、Web で出力 trace が一致する。シミュレーションを進める Web UI と外部デバイスのテストを用意する。Neovim、VS Code、Web で同じ文書の診断と定義位置が一致し、位置変換とシンボル参照を Verus で検証する |
| 4. 純粋関数型言語 | 幅に応じた回路生成、外付けインターフェイス、時系列プロパティと失敗例の再実行を実装する。受理した関数の停止、一時停止・再開を挟んだ結果の一致、マクロの束縛、外付けインターフェイスの中断と I/O 確定の規則を Verus で検証する |

## 日本語文書の推敲

Codex で設計文書を推敲する場合は、[yomiyasu v3.2.0](https://github.com/nanaism/yomiyasu/tree/v3.2.0/skills/yomiyasu) の `skills/yomiyasu/` を、作業する checkout の `.agents/skills/yomiyasu/` に置く。次のコマンドはリポジトリ直下で実行できる。既存の配置がある場合はその内容を保って終了する。

```sh
(
  set -eu
  test ! -e .agents/skills/yomiyasu || exit 0
  skill_checkout=$(mktemp -d)
  trap 'rm -rf "$skill_checkout"' EXIT
  git clone --depth 1 --branch v3.2.0 https://github.com/nanaism/yomiyasu.git "$skill_checkout"
  test "$(git -C "$skill_checkout" rev-parse HEAD)" = 3042154ee537c1b7093eefed00a97b40aae9446d
  mkdir -p .agents/skills
  cp -R "$skill_checkout/skills/yomiyasu" .agents/skills/
  printf '\n/.agents/skills/yomiyasu/\n' >> "$(git rev-parse --git-path info/exclude)"
)
```

## 参照資料

- 現行 circuitgame の [構文例](https://github.com/neknaj/circuitgame/blob/3359eff0b5e852f0321a3f101799bf5db2ddb57f/spec/sample.ncg)、[パーサー](https://github.com/neknaj/circuitgame/blob/3359eff0b5e852f0321a3f101799bf5db2ddb57f/src/rust/compiler/parser.rs)、[VM](https://github.com/neknaj/circuitgame/blob/3359eff0b5e852f0321a3f101799bf5db2ddb57f/src/rust/vm/mod.rs)、[テスト実行](https://github.com/neknaj/circuitgame/blob/3359eff0b5e852f0321a3f101799bf5db2ddb57f/src/rust/test/test.rs)
- [bem130 のソフトウェア設計指針](https://zenn.dev/bem130/articles/1b352797de94e7)
- Cargo Book の [依存指定](https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html) と [patch](https://doc.rust-lang.org/cargo/reference/overriding-dependencies.html)
- [Verus の Cargo 統合](https://verus-lang.github.io/verus/guide/cargo_verus.html)、[`no_std + alloc` で `vstd` を使う Regorus の設定](https://docs.rs/crate/regorus/0.12.0/source/Cargo.toml.orig)、[Rust の WebAssembly ターゲット](https://doc.rust-lang.org/rustc/platform-support/wasm32-unknown-unknown.html)
- [The LispKit Manual Volume 1](https://www.cs.ox.ac.uk/publications/publication3781-abstract.html)
- [Language Server Protocol の位置エンコーディング](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#position)
- [Neovim の LSP 設定](https://neovim.io/doc/user/lsp/)、[VS Code の LSP クライアント](https://code.visualstudio.com/api/language-extensions/language-server-extension-guide)、[VS Code 拡張の配布](https://code.visualstudio.com/api/working-with-extensions/publishing-extension#platform-specific-extensions)
- [共通の言語サーバーを VS Code 拡張に同梱する rust-analyzer の例](https://rust-analyzer.github.io/book/installation.html)

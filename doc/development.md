# 開発と配布

## 依存関係とリリース

配布時は Cargo の git 依存を使用する。core を参照する下流は同一 URL と同一の40桁コミット ID を `rev` に使い、対応する `version` も記す。Cargo は取得先のコミットを `rev` で選び、そのコミットのパッケージが `version` の要件を満たすか検査する。各配布側の `Cargo.lock` をコミットし、CI は `--locked`、`cargo tree -d`、lockfile の core の取得元とコミット ID、およびメインで指定したコミットの一致を確認する。

リリースでは core にタグを付けてコミット ID を確定し、GUI と CLI の依存宣言と lockfile を更新する。統合 CI は core、GUI、CLI、editors のコミット ID と、editors が使う CLI の LSP サーバーのバージョンを固定して検査する。ローカル開発では checkout を並べ、Cargo の実行ルートに適用される外部設定で `[patch."https://github.com/neknaj/circuitgame2-core"]` に path を指定する。patch 先も `version` 要件を満たす必要がある。ローカル設定と patch に伴う一時的な lockfile の差分は配布から除外する。公開 registry への移行は各クレートを公開できる状態になった時点で判断する。

[回路の統合検査](https://github.com/neknaj/circuitgame2/actions/workflows/integration.yml)は、CLI と Web が同じ Core のコミットに依存することを確かめる。CLI に付属する同じ設定と入力で、ネイティブ CLI、Wasmtime、Chromium の出力を比較する。Chromium ではフォルダーを開き、入力スイッチ、tick、リセットを操作する。公開 VRAM の例では、回路の出力と、書き込みを確定した後の記憶内容を照合する。

## ネイティブとブラウザーの GUI

共通の回路編集と実行画面は egui で実装する。ネイティブ版は OS のフォルダー選択を使い、ブラウザー版は利用者が選んだフォルダーからファイルを読む。読み込んだプロジェクトの編集、Core による実行、結果の表示は同じ Rust のコードを使う。

[GUI の CI](https://github.com/neknaj/circuitgame2-gui/actions/workflows/check.yml)では、Windows のワークスペーステストと実行ファイルのビルド、共通 GUI と従来のブラウザー版の WASM ビルドを確認する。リポジトリをまたぐ出力列の比較は、現時点では従来のブラウザー版を対象とする。

## 言語サービスと LSP

エディタに返す回路記述言語と純粋関数型言語の[診断・エラー回復・補完](diagnostics.md)は core の共通仕様に従う。LSP は core が返す位置、関連範囲、候補編集をプロトコルの型に変換する。

解析スナップショットはプロジェクト設定とソース集合を持ち、各ソースを文書 ID・版・UTF-8 テキストで識別する。サーバーは結果を返す直前に設定とソース集合の全版を照合する。LSP の補完項目の `textEdit` は文書版を運ばないため、応答後に文書が変更された場合の破棄はクライアントとの連携条件とする。版を指定して適用する修正操作には、対象文書と版を持つ `TextDocumentEdit` を使う。

言語サービスの実装は `no_std + alloc` の core に置き、Verus で検証する。両言語のコンパイラと同じ名前解決と型検査を使い、回路側では幅・結線検査も使う。定義への移動、参照検索、ホバー、セマンティックトークンもこの解析結果から求める。解析対象は文書 ID、文書バージョン、UTF-8 テキストからなるスナップショットとし、設定で指定されたソースの集合はホストが渡す。問い合わせはそのスナップショット上のバイト範囲を扱う。位置変換と定義参照は[検証設計](verification.md#仕様との対応)に従って検証する。

CLI リポジトリには `circuitgame2-lsp` を別バイナリとして置く。標準入出力の JSON-RPC、LSP メッセージと core 型の対応、ファイル URI、セッションと要求の取り消しを担当する。LSP の位置エンコーディングはクライアントと交渉し、指定がない場合は UTF-16 を使う。文字・行位置と UTF-8 byte offset の変換は core の純粋関数を呼び出す。Web エディタは同じ問い合わせを WASM 経由で使う。LSP/JSON-RPC の型は core の公開 API に含めない。

### 編集単位の増分解析

`.ncg2` と `.ncg2m` の各編集を通知順に文書へ適用し、最新の解析スナップショットを直ちに問い合わせの対象とする。複数の置換を含む通知では、一つ前の置換を適用した後の位置を使う。カーソル位置の補完やホバーと、編集中の文書の構文診断を優先し、入力の停止を待たずに処理を始める。構文診断の公開と補完の応答は、入力が途切れたことを条件とせず、結果が確定した時点で行う。変更の影響を受けた他の文書の解析と定常化推定などは後続で行い、連続した編集に対する後続処理はまとめてよい。文書全体の回復解析や時間のかかる意味解析は、中断を確認できる作業単位に分ける。ホストは編集の適用と診断の公開確定を同じイベント列で直列化し、公開確定時にスナップショットを照合する。入力が途切れたら最新版の解析を完了させる。段階ごとに診断を通知する場合、同じ版で確定した構文診断と意味診断を集約して送る。

core は文書ごとに厳格解析または回復解析の結果を保持する。未変更の文書から構文結果を再利用し、変更文書は局所再解析の条件を満たす場合に影響範囲だけを再解析する。再開位置は、隣接するトークンの結合も考慮して編集範囲より前から選ぶ。変更後のトークン列を読み進め、未変更の接尾部と字句・構文・回復の継続状態の一致が確認できた位置で、接尾部の構文を再利用する。区切り、引用、コメントの変更で一致する境界が得られない場合は、必要な範囲を広げ、文書全体の回復解析まで行う。構文の再利用単位は位置を相対範囲で保持し、親より前の編集で接尾部全体の位置を書き換える処理を省く。診断を返す際に対象版のバイト範囲へ変換する。

意味解析は宣言の見出しと本体を別々に更新する。参照側は、名前解決、型、公開状態など取得した情報に依存する。名前の検索結果には未解決や候補間の衝突を含め、優先される候補が存在しないことにも依存する。候補が追加・削除された場合は検索を再評価する。複数ファイルにある名前空間や `module-part` は、該当する宣言や断片の集合を依存先とする。型検査やマクロ展開が利用する定義も依存先に含める。変更した結果を利用する問い合わせだけに再計算を伝播し、依存先の結果が等しければ以前の意味解析結果を再利用する。診断位置と関連範囲は最新のスナップショットから求める。

問い合わせの実装には、問い合わせキーと依存を記録する読み取り API を渡す。元のスナップショットとキャッシュの内部は問い合わせエンジンのモジュールに閉じる。入力文書、設定、宣言の検索、他の問い合わせの結果は同じ API で読み取る。

性能の初期目標は、キャッシュ構築済みの状態で局所的な1回の編集を適用したとき、最初の構文診断の公開まで p95 が 16 ms 以下、カーソル位置の補完要求への応答まで p95 が 50 ms 以下である。ネイティブの release ビルドで、4,000宣言を1ファイルに置く場合と、100宣言ずつ40ファイルに置く場合を測る。測定機種、OS、ビルド条件、入力と編集列を記録する。

各シナリオでサーバーが編集や要求を受理してから診断を公開するか応答するまでの時間を測り、キュー待ちや、デバウンスによる処理開始・公開の待ち時間も含めて p50 と p95 を算出する。診断が空の場合も公開時点を記録する。局所編集に加え、括弧や引用符の削除、宣言の改名、未解決名が解決する編集、連続入力を別々に測る。連続入力では中断した版の件数と、最後の編集から最新版の診断が公開されるまでの時間も記録する。処理したバイト数、再解析した文書数、再評価した問い合わせ数を同じ条件の過去の測定と比較する。構文と意味解析の増分更新は[全体解析との一致](verification.md#編集単位の増分解析)を保証する。

### 推論結果のインレイヒント

VS Code では rust-analyzer の型表示と同じように、ソースの横に推論結果をインレイヒントとして描画する。モジュール名の直後には、[静的解析](static-analysis.md#自動解析)で上界が得られた場合に「定常化 ≤ 2 tick」のように表示する。周期解析を追加した場合は、確認できた結論に応じて「2 tick ごとに状態が戻る」または「基本周期 2 tick」と表示する。回路内の局所配線の幅や、関数型言語のローカル名の型も同じ経路で表示できる。型と実行特性の表示は個別に切り替えられる。

短いラベルに加えて、ヒントの説明に固定入力の前提、対象の内部状態、ゲート深さなどの根拠を記す。解析が未完了、対象外、または編集中の回路を確定できない場合はインライン表示を省き、要求されたときにホバーや解析コマンドでその理由を説明する。

core は表示位置、推論結果の種別とデータ、解析スナップショットを返す。LSP は要求範囲内の結果を `textDocument/inlayHint` に変換し、注釈を挿入する編集は返さない。定常化のヒントには型・引数名の種別を付けず、推論した型のヒントには型の種別を使う。本文や参照先の版が変わった場合は古い結果を破棄する。VS Code は標準のインレイヒントを使い、Neovim はクライアントが対応し利用者が有効化した場合に同じ結果を表示する。Web も core の同じデータを使う。

### Neovim と VS Code の拡張

両エディタで `.ncg2` を言語 ID `ncg2`、`.ncg2m` を言語 ID `ncg2m` として登録する。拡張は括弧の対応、コメント操作、基本的な色付けを提供し、同じ `circuitgame2-lsp` に接続する。診断、補完、ホバー、定義への移動は LSP の標準機能で提供する。基本の色付けは起動前から使え、サーバーがセマンティックトークンを提供したときは、入力ポートや回路名などを解析結果に基づいて色分けする。両言語の構文解析と型情報の計算は core が担当する。

| エディタ | editors リポジトリ内の配置 | 実装 |
| --- | --- | --- |
| Neovim 0.11 以降 | `nvim/` | Lua でファイル種別と LSP 設定を登録する。`ftplugin/` にインデントやコメントの設定、`syntax/` に基本の色付け、`lsp/circuitgame2.lua` にサーバー設定を置く。Neovim 組み込みの LSP クライアントを `vim.lsp.enable("circuitgame2")` で有効にする |
| VS Code デスクトップ | `vscode/` | `package.json` の言語宣言、言語設定、TextMate grammar、TypeScript の `vscode-languageclient` で構成する。いずれかのソース形式を開いたときに有効になり、サーバーをワークスペース側の拡張ホストで起動する |

最寄りの `circuitgame2.toml` があればその `sources` を解析する。設定がない場合と設定に含まれないファイルは単独で解析する。未保存の変更がエディタから届いていればディスク上の内容より優先する。完全修飾名と別名を経由した参照は、共通の宣言の同一性で定義移動と参照検索に対応付ける。

初回は CLI リリースにサーバーを含め、両拡張から `PATH` 上の `circuitgame2-lsp` を起動する。editors は Neovim 向けに `nvim/` をルートとするアーカイブを配布し、VS Code 向けに `.vsix` を配布する。Neovim ではアーカイブの展開先を `runtimepath` に登録する。実行ファイルのパスを指定する場合、Neovim はユーザーの LSP 設定、VS Code は実行ホストのマシン設定を使う。VS Code Remote では WSL、SSH 先、またはコンテナ側にサーバーを用意する。各拡張が対応するサーバーバージョンを公開し、editors の CI で対象の CLI リリースとの組み合わせを検査する。対応 OS・CPU のビルドが揃った段階で、CLI リリースのタグと配布ファイルのチェックサムを固定し、対象別のサーバーを同梱した VSIX を生成する。

受け入れテストでは両エディタで共通のサンプルを開き、単独ファイル、複数ソース間の完全修飾名と別名、未保存編集、日本語や絵文字を含む行で診断と定義位置が一致することを検査する。Neovim は headless で、VS Code は拡張のテストホストで起動する。サーバーを起動できない環境では基本の色付けが動作し、起動に必要な情報をユーザーへ表示する。

## Rust と Verus

core の境界は[設計概要](design.md#実装の境界)、証明の前提と対象は[検証設計](verification.md)を参照する。Verus と Rust のバージョンを固定し、`cargo verus verify` と通常の Cargo ビルドで同じ core を使う。`vstd` の機能設定、`no_std + alloc`、ブラウザ向け `wasm32-unknown-unknown` のビルドを小さな実装で確認してから依存を確定する。

## 文書の更新

仕様には受理条件・観測できる挙動・エラーを記す。必要な規則は型、判断、遷移式で定義し、境界例を添える。設計概要には実装の分担、選択の理由、未決事項を置く。主題ごとに参照する文書を決め、他の文書はその箇所へリンクする。仕様を変更したときは、対応する例と証明・試験の条件も確認する。

仕様本文では、規則が成立する入力・初期状態と、そのとき保証する結果を同じ箇所に記す。例や構文候補はそう分かる見出しや文で示す。解析に使うアルゴリズム、最適化、表示の実装は、参照する仕様の節を示して設計側に記す。例えば周期の意味は[シミュレーション仕様](simulation.md#定常状態と周期定常状態)、その周期の推定方法は[静的解析](static-analysis.md)、推定結果を信頼するための条件は[検証設計](verification.md#仕様との対応)に置く。

数式は [GitHub Docs の数式記法](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/writing-mathematical-expressions)に従う。文中ではドル記号とバッククォートを組み合わせた形式、別行では `math` コードフェンスを使う。数式内の関数名は `\mathrm{...}` で表記し、変更時は GitHub 上で表示を確認する。

## マクロ評価器の高速化

Functional but in-place（FBIP）を採用候補とする。値の変更が他の参照から観測されない条件の下で、その値に使った記憶領域を再利用する。最初は所有権で一意性を示せる構文の生成バッファ、fold の累積値、実行枠を越えて保持するスタックから試す。構文の共有参照や出所情報を保持している場合は、その部分を共有したまま新しいノードを作るか、共有されていない経路だけを更新する。

例えば、一意に所有する生成バッファへ `def` を順に追加すれば、結線を1つ追加するたびにそれまでの列を複製する処理を省ける。出力が $`N`$ 個のノードなら、少なくともその出力に相当する情報は必要になる。評価時間、割当回数、ピークメモリ、再開1回あたりの処理を、反復による大量生成、共有構文の挿入、短いマクロで測る。初版は Rust の所有権とバッファの再利用から始め、動的な参照カウントや再利用解析を導入するかは測定後に判断する。

Verus では最適化後の状態を参照評価器の状態へ対応させる。生成した構文と束縛、診断、論理ステップごとの再開結果を保存すること、共有された値が保存されることを示す。バッチ処理を行っても、実行枠で許された論理ステップまでを実行する。停止性は関数型言語の規則から引き継ぐ。

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

- [bem130 のソフトウェア設計指針](https://zenn.dev/bem130/articles/1b352797de94e7)
- Cargo Book の [依存指定](https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html) と [patch](https://doc.rust-lang.org/cargo/reference/overriding-dependencies.html)
- [Verus の Cargo 統合](https://verus-lang.github.io/verus/guide/cargo_verus.html)、[`no_std + alloc` で `vstd` を使う Regorus の設定](https://docs.rs/crate/regorus/0.12.0/source/Cargo.toml.orig)、[Rust の WebAssembly ターゲット](https://doc.rust-lang.org/rustc/platform-support/wasm32-unknown-unknown.html)
- [Language Server Protocol の位置エンコーディング](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#position)
- [Neovim の LSP 設定](https://neovim.io/doc/user/lsp/)、[VS Code の LSP クライアント](https://code.visualstudio.com/api/language-extensions/language-server-extension-guide)、[VS Code 拡張の配布](https://code.visualstudio.com/api/working-with-extensions/publishing-extension#platform-specific-extensions)
- [rust-analyzer の増分計算と問い合わせ](https://rust-analyzer.github.io/book/contributing/guide.html#salsa)
- [共通の言語サーバーを VS Code 拡張に同梱する rust-analyzer の例](https://rust-analyzer.github.io/book/installation.html)
- [VS Code の Rust インレイヒント](https://code.visualstudio.com/docs/languages/rust#_inlay-hints) と [LSP 3.17 のインレイヒント](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_inlayHint)
- [Rust Reference](https://doc.rust-lang.org/reference/) の言語仕様とツールの分離、[WebAssembly Core Specification](https://webassembly.github.io/spec/core/) の構造・検証・実行の区分を参照した。
- [W3C の Specification Guidelines](https://www.w3.org/TR/qaframe-spec/) の規則と参考記述の区分、[WebAssembly の検証アルゴリズム付録](https://webassembly.github.io/spec/core/appendix/algorithm.html) の仕様と検証方法の配置を参照した。
- [Diátaxis のリファレンス](https://diataxis.fr/reference/)、[NASA の要求記述ガイド](https://www.nasa.gov/reference/appendix-c-how-to-write-a-good-requirement/)、[arc42 の設計文書の構成](https://arc42.org/overview/)を参照した。
- [FP²: Fully In-Place Functional Programming](https://doi.org/10.1145/3607840) と [Perceus: Garbage Free Reference Counting with Reuse](https://www.microsoft.com/en-us/research/publication/perceus-garbage-free-reference-counting-with-reuse/) を、所有と記憶領域の再利用の参考にした。

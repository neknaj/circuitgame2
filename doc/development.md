# 開発と配布

## 依存関係とリリース

配布時は Cargo の git 依存を使用する。core を参照する下流は同一 URL と同一の40桁コミット ID を `rev` に使い、対応する `version` も記す。Cargo は取得先のコミットを `rev` で選び、そのコミットのパッケージが `version` の要件を満たすか検査する。各配布側の `Cargo.lock` をコミットし、CI は `--locked`、`cargo tree -d`、lockfile の core の取得元とコミット ID、およびメインで指定したコミットの一致を確認する。

リリースでは core にタグを付けて指すコミット ID を確定し、Web と CLI の依存宣言と lockfile をそれぞれ更新する。その2つのコミットをメインの専用更新 PR で指定し、まとめて検査する。ローカル開発では checkout を並べ、Cargo の実行ルートに適用される外部設定で `[patch."https://github.com/neknaj/circuitgame2-core"]` に path を指定する。patch 先も `version` 要件を満たす必要がある。ローカル設定と patch に伴う一時的な lockfile の差分は配布から除外する。公開 registry への移行は各クレートを公開できる状態になった時点で判断する。

## 言語サービスと LSP

エディタに返す回路記述言語と純粋関数型言語の[診断・エラー回復・補完](diagnostics.md)は core の共通仕様に従う。LSP は core が返す位置、関連範囲、候補編集をプロトコルの型に変換する。

サーバーは結果を返す直前に解析対象の版を照合する。LSP の補完項目の `textEdit` は文書版を運ばないため、応答後に文書が変更された場合の破棄はクライアントとの連携条件とする。版を指定して適用する修正操作には、対象文書と版を持つ `TextDocumentEdit` を使う。

言語サービスの実装は `no_std + alloc` の core に置き、Verus で検証する。両言語のコンパイラと同じ名前解決と型検査を使い、回路側では幅・結線検査も使う。定義への移動、参照検索、ホバー、セマンティックトークンもこの解析結果から求める。解析対象は文書 ID、文書バージョン、UTF-8 テキストからなるスナップショットとし、設定で指定されたソースの集合はホストが渡す。問い合わせはそのスナップショット上のバイト範囲を扱う。位置変換と定義参照は[検証設計](verification.md#仕様との対応)に従って検証する。

CLI リポジトリには `circuitgame2-lsp` を別バイナリとして置く。標準入出力の JSON-RPC、LSP メッセージと core 型の対応、ファイル URI、セッションと要求の取り消しを担当する。LSP の位置エンコーディングはクライアントと交渉し、指定がない場合は UTF-16 を使う。文字・行位置と UTF-8 byte offset の変換は core の純粋関数を呼び出す。Web エディタは同じ問い合わせを WASM 経由で使う。LSP/JSON-RPC の型は core の公開 API に含めない。

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

Verus では、最適化後の状態を参照評価器の状態へ対応させる。生成した構文と束縛、診断、論理ステップごとの再開結果を保存すること、共有された値が保存されることを示す。バッチ処理を行っても、実行枠で許された論理ステップまでを実行する。停止性は関数型言語の規則から引き継ぐ。

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
- [共通の言語サーバーを VS Code 拡張に同梱する rust-analyzer の例](https://rust-analyzer.github.io/book/installation.html)
- [VS Code の Rust インレイヒント](https://code.visualstudio.com/docs/languages/rust#_inlay-hints) と [LSP 3.17 のインレイヒント](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_inlayHint)
- [Rust Reference](https://doc.rust-lang.org/reference/) の言語仕様とツールの分離、[WebAssembly Core Specification](https://webassembly.github.io/spec/core/) の構造・検証・実行の区分を参照した。
- [W3C の Specification Guidelines](https://www.w3.org/TR/qaframe-spec/) の規則と参考記述の区分、[WebAssembly の検証アルゴリズム付録](https://webassembly.github.io/spec/core/appendix/algorithm.html) の仕様と検証方法の配置を参照した。
- [Diátaxis のリファレンス](https://diataxis.fr/reference/)、[NASA の要求記述ガイド](https://www.nasa.gov/reference/appendix-c-how-to-write-a-good-requirement/)、[arc42 の設計文書の構成](https://arc42.org/overview/)を参照した。
- [FP²: Fully In-Place Functional Programming](https://doi.org/10.1145/3607840) と [Perceus: Garbage Free Reference Counting with Reuse](https://www.microsoft.com/en-us/research/publication/perceus-garbage-free-reference-counting-with-reuse/) を、所有と記憶領域の再利用の参考にした。

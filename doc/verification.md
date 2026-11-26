# Verus による検証設計

構文解析、コンパイル、VM 実行、言語サービス、マクロ評価の各段階で証明する性質を示す。実装済みの保証は対象の入力、API、呼び出しの前提とともに示す。仕様や証明の書き方は[形式証明の実装方針](coding_standards/verification.md)を参照する。

<span id="方針"></span>

## 段階ごとに証明する性質

[ロードマップ](design.md#実装順序)の順に、解析結果、型付き回路、ネットリスト、VM 状態の間の対応をつなぐ。字句と文法には認識関係、名前解決と型付けには判断規則、回路には出力値と状態遷移の仕様を置く。仕様は検証する実行関数の返り値から独立に定義する。

| 段階 | 証明する性質 |
| --- | --- |
| 1. 構文と組み合わせ回路 | 元入力を字句と空白・コメントの範囲で覆い、厳格解析が独立した文法と同じ入力を受理する。成功時は入力全体を消費し、失敗時は最初の違反と元範囲を返す。名前解決はソースのスコープに従い、型と結線の検査では幅、ビット順、単一駆動を確かめ、回路定義の再帰を拒否する。仕様上の型が一意に決まるプログラムを資源上限内で受理する。検査済みの `func` は合法なすべての入力について出力を保存する。 |
| 2. 順序回路と RAM | `module-part` の組み立てと状態素子のインスタンス分離を検証する。ゲートを経由する配線のフィードバックを許す。reset と1 tick の対応から公開出力と VRAM の観測列の一致を導く。ラッチの保持、RAM の読み出しと書き込みの順序、他アドレスと他インスタンスの値の保存を示す。 |
| 3. CLI・GUI・LSP | 回復解析が妥当な入力で厳格解析と一致し、各修復に元範囲または合成位置の根拠があり、未処理の入力や解析枠が減ることを示す。増分解析は同じ解析対象に対する全体解析と一致し、診断・補完・定義位置はそれぞれの規則に従う。Core の位置変換には有効な範囲での往復を要求する。 |
| 4. 純粋関数型言語 | 型と循環の検査を通った対象が有限の導出で値または診断に達することを示す。実行枠を分けても評価結果を保つ。展開した構文の適合性、識別子の束縛、展開元を保存する。デバイスでは遷移の停止とポート型の適合、同じ状態・入力・時刻・イベント列に対する決定性、中断でイベントを消費せず外部要求を渡さないことを示す。 |

文法違反、値域外、資源上限は別の診断にする。深い構文や大きな展開は、ホストの呼び出しスタックへの依存を避ける。評価器の fuel は一度に進める遷移数を表す。終了までの有限性を主張する定理には、途中の遷移が存在する条件と、状態が減少する尺度を示す。Verus の `exec` の減少量検査は、呼び出し先の停止を前提とする。

## Core の公開契約で確認できる保証

以下は [Core のコミット `7bc4ad9`][core] を基準に、呼び出し側が使える契約を挙げる。段階全体の完了条件はロードマップに記す。ソースの構文、資源上限、検証済みの入口など、各契約の前提を確認して使う。

| 対象 | 公開契約から確認できること | 根拠 |
| --- | --- | --- |
| 厳格・回復解析 | `parse` は S 式の文法に対する受理と拒否、成功時の全入力の消費を保証する。`parse_recovering` は妥当な入力で同じ構文木を返し、修復がある場合は元範囲と合成位置を保持する。 | [S 式パーサー][parser] |
| ビルド用と参照用の索引 | 厳格な回路索引は同じ受理条件と診断仕様を使う。事後条件と診断の一意性の補題から、拒否時に選ぶエラー値、主範囲、関連範囲の一致を導ける。成功時の定義参照には索引の表現を比較する補題がある。 | [ビルド用索引][strict-build]・[診断の一意性][strict-error]・[定義参照][strict-refs] |
| `func` の変換と評価 | 対応するマクロなしの回路では、展開したネットリストが宣言幅の入力で返す値がソースの参照評価と一致する。 | [出力値の保存][func] |
| `module` の tick と観測 | 対応する直接・階層回路をコンパイルし、同じ配置で reset と tick を進めたとき、公開出力列がソース上の観測列と一致する。VRAM の公開名を使う観測にも対応する補題がある。 | [状態と出力列][module]・[VRAM の観測][vram] |
| 外部 I/O の確定 | Core のセッションは、準備した tick を確定したときに状態を進め、消費したイベントと渡せる要求を返す。中断では元のセッションを返す。この契約はホストに渡す要求までを扱う。 | [確定と中断][io] |
| スカラー評価 | 対応する評価には分けた実行枠を合成する補題がある。有限の評価軌跡を構成する補題には遷移の存在と条件保存が必要となる。 | [スカラー評価の実行枠と有限性][scalar] |
| マクロ展開 | 分けた実行枠を合成する補題がある。信号名・1ビット定数・基底 NOR を扱う展開後の関数では、展開順と束縛を結線検査へ渡し、生成診断を元の呼び出しに対応付ける。 | [マクロ展開の実行枠][macro]・[展開後の関数検査][mixed] |
| エディタの位置変換 | `LineIndex` は、仕様上有効な UTF-8 バイト位置と正規化済みの UTF-16 位置の往復を保証する。結果を公開する時点の文書版の照合は LSP ホストで検査する。 | [位置の往復][position] |
| 増分の参照診断 | 絶対パスの参照では、現在の検索結果と照合できた項目の診断が、新しい文書を通常どおり解決した場合と一致する。補完を含む言語サービス全体の一致は[増分解析の検証条件](verification/incremental.md)に従って広げる。 | [絶対パスの診断の再利用][editor] |

## コンパイルの正しさ

解析と型・結線の検査で、合法な入力に対するソース上の評価を定義できるようにする。型付き回路からネットリストを生成するときは、ポート順とビット順を保存する。対応表で、スライスの各ビット、`struct` のフィールドのオフセットと空きビット、RAM のインスタンスを結び付ける。

- **`func`** では、宣言の幅に合う任意の入力に対して、参照評価とネットリスト評価の出力が等しいことを示す。マクロを含む回路は元の展開結果と検査済みの配線の対応を合成する。展開済みの単純な関数を検査して既存の変換・評価契約に渡す経路と、マクロを含むソース全体から出力までの統合定理は、それぞれ適用範囲を示す。
- **`module`** では、階層を持つソース上の状態と VM の状態を対応付ける。モジュールが呼ぶ関数を構成する各基底ゲートの状態もソース側の状態に含める。reset で初期対応が成立し、同じ入力フレームの1 tick で対応を保ち、公開出力と宣言済みの VRAM を同じ値として観測できることを示す。この3条件から任意の有限入力列について観測列の一致を導く。

最適化の基準は実行経路ごとに決める。`func` の単体評価では NOR による二重否定を直結にしても同じ出力になる。`module` 内で同じ置き換えを行うと2ゲート分の伝搬が消え、入力を変えた直後の観測が変わる。`module` 内の `func` は tick ごとの観測保存を証明した変換を使う。ビットをまとめて評価する経路にも、各レーンの出力や状態が参照評価と一致する契約を与える。[ビットをまとめた NOR の契約][packed]

ゲート専用で閉路のない回路ではゲート深さから固定入力での定常化の上界を求める。各ゲートの深さと入力の深さの関係から、上界以降に状態が変わらないことを示す。状態遷移を展開して反例を探す方式を加える場合は、制約と反例の再生を同じ参照ステップに結び付ける。外部ソルバーの結論を保証に使う場合は、証明書の検査かソルバーを信頼する前提を明示する。[定常化の契約][settling]・[静的解析の仕様](static-analysis.md)

[利用者による回路の証明](circuit-proofs.md)では同じ参照意味論を使って特定の回路に必要な機能を証明する。

## 編集単位の増分解析

解析スナップショットには設定とソース集合を含め、各ソースを文書 ID・版・UTF-8 本文で識別する。同じスナップショット、問い合わせ、解析段階に対して、増分解析とキャッシュを使わない解析が同じ結果を返すことを示す。妥当な入力では共通の解析対象について厳格解析との一致も示す。[局所再解析、依存追跡、中断の検証条件](verification/incremental.md)

## 実行スナップショット

[実行スナップショット](runtime-snapshot.md)は回路を確定済みの tick から再開する保存データである。実行側の仕様では、保存しても元の状態が変わらず、互換な回路へ復元すると最後の入力から同じ出力を再現できることを求める。RAM の内容と読み出し出力は別々に保持する。read-first の書き込み直後では、読み出し出力が書き込み前の語を示すためである。

証明は順に合成する。

1. 保存内容が一つの確定済み tick の状態を表し、復元が配線、ポート順、状態素子の容量、実行条件を照合することを示す。
2. 復元後の状態との対応を1 tick の定理に渡し、同じ残り入力列で公開出力と RAM の観測列が一致することを示す。
3. バージョン付きのバイナリ形式を往復でき、長さ・バージョン・互換性が不正なときは復元先を変えずに拒否することを示す。確保量は復元先の構成から得た上限に従う。

Core の公開契約は保存した VM の状態と復元後の状態が一致すること、同じ入力列で同じ観測結果が得られることを扱う。ファイル形式の契約では互換な構成での符号化・復号の往復と、配線や周期が合わない場合の拒否を示す。確保量は復元先の構成に基づく。[VM の保存と再開](https://github.com/neknaj/circuitgame2-core/pull/101)・[ファイル形式の検証](https://github.com/neknaj/circuitgame2-core/pull/104)

ホストの結合テストでは CLI の別プロセスでの再開、CLI のファイルを Web GUI で読み込んだときの状態、IndexedDB の確定と失敗時の巻き戻しを調べる。外付けデバイスの内部状態や待ちイベントを保存する場合は、[実行スナップショットの検証項目](runtime-snapshot.md#証明と結合テスト)に従って、回路とデバイスを同じ境界から再開できることを示す。

<span id="証明の採用とレビュー"></span>

## 証明とホストの境界

Core の契約は、指定した前提の下で通常ビルドと共通の実行コードに成立する。CLI、LSP、WASM の呼び出し側では、型または実行時の検査が事前条件を満たすことを確認する。Verus の `requires` は通常の Rust ビルドで実行時検査を追加しない。[未検証の呼び出し側の方針](coding_standards/verification.md#未検証の呼び出し側)

ファイル入出力、ブラウザーのイベント処理、LSP の版照合、実機の通信、GPU の実行環境はホストとの境界にある。対応するネイティブ・WASI・ブラウザー・実機などの結合テストで確認する。環境ごとの性能は計測する。Core に入る値や状態については、証明できる性質を公開契約へつなぐ。[証明とテストの役割](coding_standards/verification.md#証明とテストの役割)

Core の CI では固定版 Verus と `--no-cheating` でワークスペースを検証し、追跡済みの Rust ソースから仮定や検査除外も監査する。通常の Rust のテストと対象向けのビルドも実行する。CI の成功は対象コミットのコードとその契約・仮定に対応する。[Core の検査ワークフロー][ci]・[仮定とレビューの方針](coding_standards/verification.md#仮定とレビュー)

## 仕様との対応

| 対象 | 参照する仕様 |
| --- | --- |
| 字句、構文、名前解決、回路の型・結線 | [文法](grammar.md)・[回路言語](circuit-language.md)・[名前解決](names.md#検証する性質) |
| 参照ステップ、ラッチと RAM、時刻、保存・復元 | [シミュレーション](simulation.md)・[実行スナップショット](runtime-snapshot.md) |
| 要求と応答、単一駆動、初期化、reset 世代の識別 | [外部 I/O](memory-io.md)・[デバイス契約](device-contract.md) |
| 型と評価結果、評価の停止と再開、マクロの束縛 | [関数型言語の型検査](functional-types.md)・[関数型言語の評価とマクロ](macros.md) |
| 診断・回復・補完、インレイヒントの位置と版 | [診断と補完](diagnostics.md)・[インレイヒント](development.md#推論結果のインレイヒント) |

## 参照資料

- [Verus のガイド](https://verus-lang.github.io/verus/guide/)
- [Vest の検証付きパーサー・シリアライザー](https://www.usenix.org/conference/usenixsecurity25/presentation/cai-yifeng)
- [CompCert の意味保存](https://compcert.org/man/manual001.html)
- [Biere らの Bounded Model Checking](https://ix.cs.uoregon.edu/~michal/Classes/04u/fsv/readings/Biere-BMC.pdf)

[core]: https://github.com/neknaj/circuitgame2-core/tree/7bc4ad9614a5717b7221aa6902833e08245faa10
[parser]: https://github.com/neknaj/circuitgame2-core/blob/7bc4ad9/crates/syntax/src/lib.rs#L576-L629
[strict-build]: https://github.com/neknaj/circuitgame2-core/blob/7bc4ad9/crates/syntax/src/circuit/build.rs#L807-L820
[strict-error]: https://github.com/neknaj/circuitgame2-core/blob/7bc4ad9/crates/syntax/src/circuit/index.rs#L301-L312
[strict-refs]: https://github.com/neknaj/circuitgame2-core/blob/7bc4ad9/crates/syntax/src/circuit/definitions.rs#L92
[func]: https://github.com/neknaj/circuitgame2-core/blob/7bc4ad9/src/project/use_aliases/bit_func/compile.rs#L310-L325
[module]: https://github.com/neknaj/circuitgame2-core/blob/7bc4ad9/src/project/use_aliases/module_types/vm_source/execution.rs#L578-L595
[vram]: https://github.com/neknaj/circuitgame2-core/blob/7bc4ad9/src/project/use_aliases/module_types/vm_source/execution/vram_binding.rs#L352
[io]: https://github.com/neknaj/circuitgame2-core/blob/7bc4ad9/src/device/state_session/owned_tick.rs#L214-L277
[scalar]: https://github.com/neknaj/circuitgame2-core/blob/7bc4ad9/src/ncg2m/call_evaluation/scalar/execution/slice.rs#L282-L372
[macro]: https://github.com/neknaj/circuitgame2-core/blob/7bc4ad9/src/ncg2m/call_evaluation/macro_expansion.rs#L437-L449
[mixed]: https://github.com/neknaj/circuitgame2-core/blob/7bc4ad9/src/project/use_aliases/bit_func/generated/mixed_body.rs#L790-L800
[editor]: https://github.com/neknaj/circuitgame2-core/blob/7bc4ad9/src/project/use_aliases/definitions/observations.rs#L423-L430
[packed]: https://github.com/neknaj/circuitgame2-core/blob/7bc4ad9/src/netlist/bit_sliced.rs#L215
[settling]: https://github.com/neknaj/circuitgame2-core/blob/7bc4ad9/src/project/use_aliases/settling.rs#L321
[ci]: https://github.com/neknaj/circuitgame2-core/blob/7bc4ad9/.github/workflows/ci.yml
[position]: https://github.com/neknaj/circuitgame2-core/blob/7bc4ad9/src/editor/lines.rs#L640-L721

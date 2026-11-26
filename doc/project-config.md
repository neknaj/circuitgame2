# プロジェクトの実行設定

プロジェクトの設定は `circuitgame2.toml` に記す。ファイルは TOML 1.0 とし、相対パスは設定ファイルがあるディレクトリを基準に解決する。LSP のプロジェクト探索は[開発と配布](development.md#neovim-と-vs-code-の拡張)を参照する。

```toml
sources = ["main.ncg2", "logic.ncg2", "devices.ncg2m"]
entry = "::main"
tick-ns = { numerator = 10, denominator = 1 }
state-bits = 8388608

[[device]]
name = "terminal"
kind = "uart-terminal"
bindings = { tx = "uart-tx", rx = "uart-rx" }
options = { baud = 115200 }

[[vram]]
name = "screen"
read-output = "fb-read"
```

| 項目 | 意味 |
| --- | --- |
| `sources` | 必須。1件以上の仮想相対パスを列挙する。拡張子とパスを [ソース集合の規則](names.md#ソース集合) に従って検査する |
| `entry` | 省略時は `::main`。ルートとして実行する回路の `module` を完全修飾名で指定する |
| `tick-ns` | 正の整数の分子・分母で表す、1 tick あたりのナノ秒。時間指定を使うデバイスを接続する場合は必須 |
| `state-bits` | 順序回路の状態に使える総ビット数。1から4,294,967,295まで。省略時は8,388,608ビット |
| `device` | 省略可能な配列。各要素に一意の `name`、デバイスの `kind`、デバイス側のポート名からルート側のポート名への `bindings` を指定する。`options` はデバイス固有で省略可能 |
| `vram` | 省略可能な配列。各要素に公開名 `name` と対象の RAM の読み出し信号 `read-output` を指定する |

`kind` は[登録済みのデバイス種別](device-contract.md#デバイス種別とインスタンス)を指定する。`bindings` の方向と型は選択したデバイスのポート宣言とルートモジュールから決める。未知のデバイスやポート、必要な接続の不足、型または方向の不一致、入力の重複駆動は設定の検査で報告する。デバイス固有のオプションはデバイスの仕様に従う。実行倍率は実行環境の操作で変更し、論理 tick やイベントの適用時刻は[シミュレーション仕様](simulation.md#実行速度)に従う。

フィールド名の誤記を検出できるよう、上の表と各フィールドの定義にないキーは設定エラーとする。`options` 内のキーは選択したデバイスが検査する。`tick-ns` の分子・分母はそれぞれ1以上、符号付き64ビット整数の最大値以下とする。

`state-bits` と照合するのは、全 RAM の記憶内容と各 RAM が保持する読み出し値、全ラッチの保持値を合算したビット数である。上限を超える回路は実行開始前に診断する。確保する量は回路の構成で決まり、上限以内でも実行環境に空きがなければ確保に失敗する。

初版の `read-output` はルートモジュール本体で `memory` を直接呼んだ `def` の単一出力名を指定する。例えば `(def fb-read (framebuffer address pixels write-enable))` で `framebuffer` が `memory` の宣言名なら、`fb-read` がその RAM インスタンスを特定する。容量と1語の型は素子の宣言から取得する。表示側が参照するのは最後に確定した tick の RAM 内容であり、公開設定により書き込み権限が追加されることはない。

プロジェクト設定を使わず単独ファイルを実行する場合は、そのファイルをソース集合とし、`::main` を選ぶ。外部デバイスの接続にはプロジェクト設定を使う。CLI と GUI はそれぞれの実行環境で設定ファイルを読み込む。TOML の解析には Core ワークスペースの `circuitgame2-project-config` を共用する。構成の意味検査は Core が行う。

- [TOML 1.0 仕様](https://toml.io/en/v1.0.0)

# Neknaj Circuit Game 2

Neknaj Circuit Game 2 は、circuitgame の後継として論理回路記述言語 NCG2 とそのシミュレーターを開発するプロジェクト。CLI で組み合わせ回路を評価でき、順序回路は CLI とブラウザーで 1 tick ずつ実行できる。このリポジトリには言語仕様、開発計画、サンプルを置く。

## CLI で回路を試す

Git と Rustup を用意し、CLI と付属の例題を取得する。

```sh
git clone https://github.com/neknaj/circuitgame2-cli.git
cd circuitgame2-cli
cargo install --path . --locked
ncg2 --version
```

`ncg2` が見つからない場合は、Cargo が示す実行ファイルの保存先を `PATH` に加える。

### NOR 回路を検査して評価する

引き続き `circuitgame2-cli` ディレクトリで実行する。

```sh
ncg2 check examples/nor.ncg2
ncg2 eval --func ::gate --input 00 examples/nor.ncg2
```

検査に成功すると `検査成功（1 ファイル）` と表示される。続く評価では、入力が両方 0 のときの NOR の出力 `1` が表示される。

### 順序回路を実行する

```sh
ncg2 run --input 0110 --input 1000 examples/selected-latch.ncg2
```

```text
0 00
1 01
2 01
```

1 列目は tick 番号で、0 はリセット直後を表す。2 列目には出力ビット列が並ぶ。`--input` 一つにつき 1 tick 進む。この例では 1 tick 目にラッチへ `01` を書き込み、2 tick 目も値を保持する。

CLI の README には、複数ファイルのプロジェクトを実行する手順、RAM の内容を読む例、定常化を調べる方法を掲載している。 [CLI の使い方](https://github.com/neknaj/circuitgame2-cli#readme)

## ブラウザーで回路を試す

[公開 GUI](https://neknaj.github.io/circuitgame2-gui/) を開くと、付属の回路を編集し、入力を切り替えながら 1 tick ずつ実行できる。自分のプロジェクトを開くには「Open project folder」で `circuitgame2.toml` のあるフォルダーを選ぶ。同じ GUI をネイティブで起動する手順もある。 [GUI の使い方](https://github.com/neknaj/circuitgame2-gui#readme)

## エディタで回路を書く

VS Code または Neovim の拡張と `circuitgame2-lsp` をインストールすると、`.ncg2` ファイルで診断と定義移動を使える。 [エディタ拡張の入手と設定](https://github.com/neknaj/circuitgame2-editors#readme)

## サンプルプロジェクト

- 半加算器で、lib の回路を使う。
- 自律 UART 送信機が `Hello, world!` を送る波形を CLI で取得し、9600 baud の 8N1 として復号する。
- NCG2 の加減算回路と、Python で模擬したキー行列・I²C 接続の 7 セグメント LCD を組み合わせて電卓を動かす。

各サンプルの起動方法と、必要なライブラリの取得手順を掲載している。 [サンプル一覧](examples/) · [回路と補助関数のライブラリ](https://github.com/neknaj/circuitgame2-lib#readme)

## 設計と仕様を読む

- [ブラウザーで読む（mdBook）](https://neknaj.github.io/circuitgame2/docs/)
- [設計文書の案内と実装順序](doc/design.md)
- [開発と配布](doc/development.md)

Rust から Core を使う例と、開発時に実行する検証コマンドを掲載している。 [Core の README](https://github.com/neknaj/circuitgame2-core#readme)

プロジェクト全体の仕様やサンプルの不具合・質問は root repo で受け付ける。CLI、GUI、エディタ拡張に固有の内容は、それぞれのリポジトリに報告できる。 [プロジェクトの Issues](https://github.com/neknaj/circuitgame2/issues)

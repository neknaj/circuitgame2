# Neknaj Circuit Game 2

neknaj circuit game 2 は、circuitgame の後継となる論理回路記述言語 NCG2 と、そのシミュレーターを開発するプロジェクトである。このリポジトリでは NCG2 の仕様と開発計画を管理する。

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

### 定常化を調べる

付属のプロジェクトで、入力を固定してから 1 tick 以内に状態が定常化することを確認する。

```sh
ncg2 settle --project examples/project/circuitgame2.toml --within 1
```

CLI の README に、自分のファイルを実行する手順、ビットの並べ方、同じ子モジュールを二度呼ぶ RAM の例題を載せている。設定ファイルでソースを指定し、公開した RAM の内容を表示する手順も試せる。[CLI の README](https://github.com/neknaj/circuitgame2-cli#readme)
CLI の不具合や質問は [CLI の Issues](https://github.com/neknaj/circuitgame2-cli/issues) に投稿できる。

## 設計と仕様を読む

- [ブラウザーで読む（mdBook）](https://neknaj.github.io/circuitgame2/docs/)
- [設計文書の案内と実装順序](doc/design.md)
- [開発と配布](doc/development.md)

CLI と Web で共用する Rust ライブラリの使用例と検証コマンドは [core の README](https://github.com/neknaj/circuitgame2-core#readme) にある。

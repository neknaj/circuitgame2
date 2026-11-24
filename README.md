# circuitgame2

circuitgame の後継となる論理回路記述言語 NCG2 と、そのシミュレーターを開発するプロジェクト。このリポジトリでは NCG2 の仕様と開発計画を管理する。

## CLI で試す

Rustup と Git を用意し、CLI リポジトリを取得して、付属する NOR の例題を検査・評価する。

```sh
git clone https://github.com/neknaj/circuitgame2-cli.git
cd circuitgame2-cli
git checkout --detach 1924a245a751ef11e0f853499745001eae93bc6c
cargo run --quiet --locked -- check examples/nor.ncg2
cargo run --quiet --locked -- eval --func ::gate --input 00 examples/nor.ncg2
```

検査に成功すると `検査成功（1 ファイル）` と表示される。最後のコマンドは、入力が両方 0 のときの NOR の出力 `1` を表示する。自分のソースを検査する方法や入力ビットの並べ方は [CLI の README](https://github.com/neknaj/circuitgame2-cli/tree/1924a245a751ef11e0f853499745001eae93bc6c#readme) にある。

### 順序回路を試す

順序回路の実行は、開発版 CLI の `stage2/clocked-run` ブランチで試せる。上の手順で取得した `circuitgame2-cli` のディレクトリで実行する。

```sh
git fetch origin stage2/clocked-run
git checkout --detach 7312ad4a0f6bf2eb57229873a5f2ac0b73483d54
cargo run --quiet --locked -- run --input 11 --input 00 examples/latch.ncg2
```

```text
0 00
1 11
2 10
```

`(def q held)` は、後に定義するラッチ出力 `held` を `q` へ直結する。1 tick 目にラッチへ 1 を書き込み、2 tick 目はその値を保持する。2 番目の出力は各 tick の開始時点における `q` の反転である。

入出力のビットはポートの宣言順に、各ポート内では最下位ビットから並べる。`--input` の指定ごとに 1 tick 進める。出力の1列目は tick 番号で、0 はリセット直後を表す。2列目は出力ビットである。`def` の右辺には信号名による直結と、基底 NOR、ラッチ、RAM の直接呼び出しを書ける。実引数には信号名、ビットリテラル、信号名を起点にした `bit` と `slice` を使える。オプションは [CLI の README](https://github.com/neknaj/circuitgame2-cli/tree/7312ad4a0f6bf2eb57229873a5f2ac0b73483d54#readme) にある。

## 設計と仕様を読む

- [ブラウザーで読む（mdBook）](https://neknaj.github.io/circuitgame2/docs/)
- [設計文書の案内と実装順序](doc/design.md)
- [開発と配布](doc/development.md)

CLI と Web で共用する Rust ライブラリの使用例と検証コマンドは [core の README](https://github.com/neknaj/circuitgame2-core#readme) にある。

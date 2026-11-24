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

## 設計と仕様を読む

- [ブラウザーで読む（mdBook）](https://neknaj.github.io/circuitgame2/docs/)
- [設計文書の案内と実装順序](doc/design.md)
- [開発と配布](doc/development.md)

CLI と Web で共用する Rust ライブラリの使用例と検証コマンドは [core の README](https://github.com/neknaj/circuitgame2-core#readme) にある。

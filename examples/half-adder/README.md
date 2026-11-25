# 半加算器

二つの 1 ビット入力を受け取り、和と桁上がりを返す。回路は lib の公開関数 `::ncg2lib::logic::xor` と `::ncg2lib::logic::and` を呼び出す。

このディレクトリで [lib の取得手順](../README.md#使い方)を実行する。

```sh
ncg2 eval --func ::half-adder --input 11 --project circuitgame2.toml
```

出力の順序は和、桁上がりである。入力 `00`、`01`、`10`、`11` に対して、出力は順に `00`、`10`、`10`、`01` になる。

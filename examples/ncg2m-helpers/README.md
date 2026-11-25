# NCG2M の補助関数を評価する

`::demo::may-run` は準備済み（`ready`）でブロックされていない（`blocked` が `false`）ときに `true` を返す。lib の `not` を `invert` という別名で呼び、`and` は完全修飾名で呼ぶ。

`eval-meta` に対応した `ncg2` を使う。このディレクトリで [lib の取得手順](../README.md#使い方)を実行し、次のように二つの引数を渡す。

```sh
ncg2 eval-meta --defn ::demo::may-run --arg true --arg false --project circuitgame2.toml
ncg2 eval-meta --defn ::demo::may-run --arg true --arg true --project circuitgame2.toml
```

最初のコマンドは `true`、二つ目は `false` を1行に出力する。`--arg` は署名の引数と同じ順に指定する。

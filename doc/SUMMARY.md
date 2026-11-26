# 目次

[設計概要](design.md)

# 言語仕様

- [字句規則と文法](grammar.md)
- [ソースの整形](formatting.md)
- [回路言語](circuit-language.md)
- [ソース集合と名前解決](names.md)
- [関数型言語の型検査](functional-types.md)
- [関数型言語の評価とマクロ](macros.md)

# 実行と外部 I/O

- [シミュレーション](simulation.md)
  - [実行スナップショット](runtime-snapshot.md)
  - [GPU と RP マイコンの実行バックエンド](backends.md)
- [プロジェクトの実行設定](project-config.md)
- [外部 I/O とメモリ](memory-io.md)
  - [デバイスの初期化とホスト境界](device-contract.md)
  - [標準の入出力デバイス](peripherals.md)
    - [I²C 接続の7セグメント LCD](peripherals/i2c-pcf8576d.md)

# 解析と検証

- [定常化と周期の静的解析](static-analysis.md)
- [診断と補完](diagnostics.md)
- [Verus による検証設計](verification.md)
- [利用者による回路の証明](circuit-proofs.md)

# 開発

- [開発と配布](development.md)
  - [ドキュメントの書き方とプレビュー](writing.md)
- [形式証明の実装方針](coding_standards/verification.md)
- [Rust と Verus のコメント](coding_standards/comments.md)

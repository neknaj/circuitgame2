# ドキュメントの書き方とプレビュー

設計と仕様の原稿は `doc/` の Markdown に置く。章を追加したときは `doc/SUMMARY.md` に登録する。目次では、概要から仕様や検証に進めるように、関連する章を部にまとめる。

## 章を書く

章の冒頭に、読者が何を調べられるかを書く。見出しは「概要」のような一般語だけで済ませず、「ソース集合の決定」「参照先が見つからない場合」のように節の内容を示す。見出しの階層は順に下げる。章から章へのリンクには、参照する規則や手順の名前を使う。

仕様では成立条件、観測できる結果、失敗時の診断をまとめ、例や境界値を添える。実装案は適用する仕様へリンクする。既存の用語、数式、証明との対応は[文書の更新方針](development.md#文書の更新)に従う。

## 手元で表示を確認する

Python 3.8 以降と mdBook 0.5.4 を使う。Cargo から入れる場合は、リポジトリのルートで次を実行する。

```sh
cargo install mdbook --version 0.5.4 --locked
mdbook serve
```

`http://localhost:3000` で章間リンクや数式の表示を確かめる。`mdbook build` は `book/` に HTML を生成する。原稿の数式は GitHub の記法で書く。ビルドで数式の区切りを変換し、ブラウザーで MathJax が数式を表示する。

参考資料は [mdBook の目次の仕様](https://rust-lang.github.io/mdBook/format/summary.html)、[見出しとページ構成の指針](https://developers.google.com/style/headings)、[リンク文の指針](https://developers.google.com/style/link-text) を参照する。

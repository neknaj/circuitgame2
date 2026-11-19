# Rust と Verus のコメント

## 実装コメント

実装上の判断とその理由は対象の処理の直前に独立した `//` 行で記す。コードから読み取れる操作を言い直すだけのコメントは省く。分岐の順序や数値の根拠、仕様上の例外を説明するときは、対応する仕様の節を示す。例えば、回復時に不正な文字列内の括弧を読み飛ばす理由は [エラー回復の仕様](../diagnostics.md#エラー回復)に対応付ける。

`unsafe` ブロックには `// SAFETY:` を付け、その箇所で必要な安全条件と、それを満たす根拠を書く。条件の一部を呼び出し側が満たす場合は、関数の `# Safety` から追えるようにする。

## ドキュメントコメント

クレートやモジュール全体には `//!`、個々の公開項目には `///` を使う。冒頭の一文で役割を示し、空行のあとに利用条件と観測できる挙動を記す。引数と戻り値の型を繰り返すより、UTF-8 の半開バイト範囲、構文木の要素順、失敗後の状態など、型から読み取れない情報を説明する。非公開項目でも、複数の呼び出し元が依存する契約は項目の近くに記す。

エラーを返す条件は `# Errors`、パニックする条件は `# Panics`、呼び出し側が守る安全条件は `# Safety` に記す。これらの節は該当する場合に設ける。使用例を示す場合は `# Examples` に置き、Rust の例は通常のドキュメントテストで検査できる形にする。失敗し得る処理の例では用途に応じて `?` でエラーを伝える。同じ例が複数の項目に当てはまるときは、共通の例にリンクできる。

## Verus の証明に添えるコメント

検証に必要な条件は `requires`、`ensures`、不変条件、減少量、補題としてコードに記す。コメントには、条件がどの仕様を表すか、非自明な不変条件がどの処理で保たれるか、補題をどの保証につなげるかを記す。ソルバーに与える補助アサーションの目的が読み取りにくいときは、必要な事実を示す。仮定の記録や証明の範囲は [形式証明の実装方針](verification.md)に従う。

## 参照資料

- [Rust Reference のコメント構文](https://doc.rust-lang.org/reference/comments.html)
- [Rust Style Guide のコメント規則](https://doc.rust-lang.org/stable/style-guide/#comments)
- [rustdoc Book の文書の書き方](https://doc.rust-lang.org/rustdoc/how-to-write-documentation.html)
- [Rust API Guidelines の文書規則](https://rust-lang.github.io/api-guidelines/documentation.html)
- [Verus の事前条件・事後条件・アサーション](https://verus-lang.github.io/verus/guide/requires_ensures.html)

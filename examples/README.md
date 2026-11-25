# サンプルプロジェクト

| 例 | 試せること |
| --- | --- |
| [半加算器](half-adder/) | lib の XOR と AND を呼び出し、4 通りの入力を検査する |
| [UART で Hello, world!](uart-hello/) | バイトとビット位置を組み合わせ回路に渡して 8N1 を復号する |
| [順序回路で UART 送信](clocked-uart-transmitter/) | 回路が自律送信する 9600 baud の波形を復号する |
| [キー行列と I²C 接続の LCD で動かす電卓](keypad-calculator/) | キーを行ごとに読み取り、NCG2 で加減算し、7 セグメントの表示を更新する |
| [Pico と Pico 2 の GPIO 回路](rp-gpio/) | 名前付き回路ポートをボードの GPIO に結び付け、ファームウェアの配線表を作る |

## 使い方

[CLI の導入手順](../README.md#cli-で回路を試す)に従い、`ncg2` をインストールする。
実行したい例のディレクトリに移動し、初回だけ lib repo の回路ソースを取得する。

```sh
git clone https://github.com/neknaj/circuitgame2-lib.git vendor/circuitgame2-lib
git -C vendor/circuitgame2-lib checkout --detach 8d31e170f301a2e8900066eaea3dbf23643c8878
ncg2 check --project circuitgame2.toml
```

各例の `circuitgame2.toml` は、例題のソースと lib の回路ソースをプロジェクト内の相対パスで参照する。取得した lib repo は Git の管理対象外とする。

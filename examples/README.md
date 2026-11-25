# サンプルプロジェクト

| 例 | 試せること |
| --- | --- |
| [半加算器](half-adder/) | lib の XOR と AND を呼び出し、4 通りの入力を検査する |
| [NCG2M の補助関数](ncg2m-helpers/) | lib の公開関数を呼ぶ補助関数を `ncg2 eval-meta` で評価する |
| [UART で Hello, world!](uart-hello/) | バイトとビット位置を組み合わせ回路に渡して 8N1 を復号する |
| [順序回路で UART 送信](clocked-uart-transmitter/) | 回路が自律送信する 9600 baud の波形を復号する |
| [キー行列と I²C 接続の LCD で動かす電卓](keypad-calculator/) | キーを行ごとに読み取り、NCG2 で加減算し、7 セグメントの表示を更新する |
| [Pico と Pico 2 の GPIO 回路](rp-gpio/) | 名前付き回路ポートをボードの GPIO に結び付け、ファームウェアの配線表を作る |
| [Pico と Pico 2 の UART エコー](rp-uart-loopback/) | ボードの実 UART で受け取った1バイトを送り返す |
| [Pico と Pico 2 で LM75B の設定を読む](rp-i2c-lm75b/) | ハードウェア I²C で設定レジスタを読み、回路の出力を GPIO で観測する |

## 使い方

[CLI の導入手順](../README.md#cli-で回路を試す)に従い、`ncg2` をインストールする。
各例のディレクトリで README の手順を実行する。lib を使う例では初回だけ、次のように lib repo のソースを取得する。

```sh
git clone https://github.com/neknaj/circuitgame2-lib.git vendor/circuitgame2-lib
git -C vendor/circuitgame2-lib checkout --detach 8d31e170f301a2e8900066eaea3dbf23643c8878
ncg2 check --project circuitgame2.toml
```

lib を使う例の `circuitgame2.toml` は、例題と lib のソースをプロジェクト内の相対パスで参照する。取得した lib repo は Git の管理対象外とする。

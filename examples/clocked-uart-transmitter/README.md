# 順序回路で UART 送信

入力ポートのない NCG2 回路が 9600 baud・8N1 で `Hello, world!` を一度送信する。回路の中で送信間隔を作り、13 文字を順に送り出す。

このディレクトリで [lib の取得手順](../README.md#使い方)を実行する。`--ticks` に対応した `ncg2` と Python 3 を使う。

```sh
python demo.py
```

```text
Hello, world!
```

tick 番号と TX の値を直接見るには、次のコマンドを実行する。

```sh
ncg2 run --project circuitgame2.toml --ticks 17000
```

## 送信のしくみ

1. NOR と63段のラッチに信号を戻すと、64 tick ごとに値が反転する。立ち下がりを拾うと、128 tick ごとに1回の送信パルスが得られる。
2. 最初のパルスで、13 個のシフトレジスターに1文字分ずつのフレームを読み込む。各フレームは Low の開始ビット、最下位ビットから順に並べたデータ8ビット、High の停止ビットで構成する。パリティは付けない。[Microchip の UART 非同期モード](https://onlinedocs.microchip.com/oxy/GUID-D364745C-8255-47AE-9528-9EB17646EE19-en-US-18/GUID-F37FDF72-1D87-438A-A2F1-D70FD2AC07AC.html)
3. 次のパルスからは1ビットずつ送り出す。末尾に High に対応する値を補うので、送信後も TX は High を保つ。

`circuitgame2.toml` の tick 周期は 78125/96 ns。128 tick が 1/9600 秒に一致する。[シミュレーションの時間仕様](../../doc/simulation.md#tick-とシミュレーション時間)

reset 直後の tick 0 は NOR の出力が0で、tick 1 に TX がアイドルの High になる。最初の開始ビットは tick 69 に現れる。Python はアイドル後の立ち下がりを探し、各ビットの 128 tick をすべて照合してから復号する。停止ビットと送信後のアイドルも検査する。観測対象はシミュレーション上の TX の論理値。

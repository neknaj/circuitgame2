# UART で Hello, world!

NCG2 の `::uart-bit` に送信する ASCII バイトとビット位置を渡す。回路は lib の論理回路を使い、開始ビット、データ8ビット、停止ビットを選ぶ。データは最下位ビットから送り、パリティは付けない。

このディレクトリで [lib の取得手順](../README.md#使い方)を実行し、Python 3 で試す。

```sh
python demo.py
```

```text
Hello, world!
```

スクリプトがバイトと位置を順に供給し、`ncg2 eval` の 1 ビット出力を受信側で復号する。波形は 1 ビット期間ごとの論理値で、シリアルポートの駆動とビット周期の設定は含まない。

[Microchip の UART 非同期モード](https://onlinedocs.microchip.com/oxy/GUID-D364745C-8255-47AE-9528-9EB17646EE19-en-US-18/GUID-F37FDF72-1D87-438A-A2F1-D70FD2AC07AC.html)

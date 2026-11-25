# Pico と Pico 2 で動く GPIO 回路

GP5 に GP2 の反転値を出す。GP3 と GP4 には、1 tick 前の GP5 の回路値と現在の GP7 の値を NOR で計算して出す。起動時に GP3 は High、GP4 と GP5 は Low になる。最初の tick から回路の出力が各ピンに反映される。

## 配線表を作る

このディレクトリで [サンプル共通の lib 取得手順](../README.md#使い方)を実行し、`rp-plan` に対応した `ncg2` を使う。通常のプロジェクト設定は `circuitgame2.toml`、ボード設定は `board.toml` にある。Pico を使う場合は、ボード設定の `board` を `"pico"` にする。

```sh
ncg2 rp-plan --project circuitgame2.toml --board board.toml > rp-plan.txt
```

Windows PowerShell では、次の手順で配線表を UTF-8 で保存する。

```powershell
$plan = ncg2 rp-plan --project circuitgame2.toml --board board.toml
if ($LASTEXITCODE -ne 0) { throw "配線表を生成できない" }
[IO.File]::WriteAllLines((Join-Path $PWD.Path 'rp-plan.txt'), [string[]]$plan, [Text.UTF8Encoding]::new($false))
```

## ファームウェアをビルドする

`NCG2_RP_PROGRAM` に配線表の絶対パスを指定して、[Core の RP ファームウェア](https://github.com/neknaj/circuitgame2-core/tree/main/firmware/rp)をビルドする。Pico 2 は `pico2` と `thumbv8m.main-none-eabihf`、Pico は `pico` と `thumbv6m-none-eabi` を選ぶ。UF2 に変換するときのファミリーもボードに合わせる。

Windows PowerShell では配線表を生成したディレクトリで絶対パスを取得してからビルドする。次は Pico 2 の例。Core を別の場所に置いた場合はマニフェストのパスを調整する。

```powershell
$env:NCG2_RP_PROGRAM = (Resolve-Path ./rp-plan.txt).Path
cargo +1.99.1 build --manifest-path ../../../circuitgame2-core/firmware/rp/Cargo.toml --locked --release --target thumbv8m.main-none-eabihf --features pico2
```

GND を共通にし、3.3 V ロジックで GP2 と GP7 を駆動する。GP3・GP4・GP5 はロジックアナライザーで観測する。 [ボードのピン配置](https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html)

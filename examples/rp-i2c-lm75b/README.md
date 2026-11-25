# Pico と Pico 2 で LM75B の設定を読む

GP2 に接続したボタンを押している間、I²C で LM75B の設定レジスタを繰り返し読む。応答が届いた tick に設定の最下位ビットを GP5 に出す。応答がない tick や初期設定の値を受け取った tick は Low になる。 [LM75B のレジスタ仕様](https://www.nxp.com/docs/en/data-sheet/LM75B.pdf)

LM75B は 3.3 V で動かし、Pico と GND を共通にする。LM75B のアドレス端子 A2〜A0 を GND につなぐ。SDA を GP0、SCL を GP1 につなぎ、両方を 3.3 V にプルアップする。GP2 と 3.3 V の間にボタンをつなぐ。GP2 はファームウェアが内部プルダウンを有効にする。

## ファームウェアをビルドする

I²C 対応の CLI と core repo を使う。Pico で試す場合は `board.toml` の `board` を `"pico"` に変更する。このディレクトリで配線表を作る。

```powershell
$plan = ncg2 rp-plan --project circuitgame2.toml --board board.toml
if ($LASTEXITCODE -ne 0) { throw "配線表を生成できない" }
[IO.File]::WriteAllLines((Join-Path $PWD.Path 'rp-plan.txt'), [string[]]$plan, [Text.UTF8Encoding]::new($false))
$env:NCG2_RP_PROGRAM = (Resolve-Path ./rp-plan.txt).Path
```

Core の位置に合わせて `--manifest-path` を調整し、ボードに対応するターゲットを Rust 1.99.1 に追加してビルドする。

| ボード | Cargo の `--target` | `--features` | UF2 ファミリー |
| --- | --- | --- | --- |
| Pico | `thumbv6m-none-eabi` | `pico,i2c` | `rp2040` |
| Pico 2 | `thumbv8m.main-none-eabihf` | `pico2,i2c` | `rp2350-arm-s` |

```powershell
rustup target add --toolchain 1.99.1 thumbv8m.main-none-eabihf
cargo +1.99.1 build --manifest-path ../../../circuitgame2-core/firmware/rp/Cargo.toml --locked --release --target thumbv8m.main-none-eabihf --features pico2,i2c --bin ncg2-rp
```

生成した `ncg2-rp` を UF2 に変換し、BOOTSEL で読み込む。 [Core の UF2 変換手順](https://github.com/neknaj/circuitgame2-core/tree/main/firmware/rp#ビルド)

ロジックアナライザーでは アドレス `0x48` にポインター `0x01` を書いたあと、反復 START を挟んで1バイト読む取引を確認できる。物理アドレス、送受信長、ポインターは回路の出力として `board.toml` に割り当てている。

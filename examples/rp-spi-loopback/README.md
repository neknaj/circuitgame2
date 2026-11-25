# Pico と Pico 2 の SPI 折り返し

起動すると SPI0 で `0x96` を1バイトずつ繰り返し送る。MOSI の GP19 と MISO の GP16 をジャンパー線でつなぐと、送信したバイトが受信側に戻る。

ロジックアナライザーの GND をボードの GND につなぐと、CS（GP20）、SCK（GP18）、MOSI（GP19）、MISO（GP16）を観測できる。設定は 1 MHz、モード3で、最上位ビットから `10010110` の順に転送する。

GP5 には受信バイトのビット1を出す。折り返しが成功した応答の tick では High、応答がない tick や転送に失敗した tick では Low になる。

## ファームウェアをビルドする

SPI 対応の `ncg2` と Core を使う。サンプルのディレクトリで Pico 2 用の配線表を作る。Pico で試す場合は、先に `board.toml` の `board` を `"pico"` に変更する。

```powershell
$plan = ncg2 rp-plan --project circuitgame2.toml --board board.toml
if ($LASTEXITCODE -ne 0) { throw "配線表を生成できない" }
[IO.File]::WriteAllLines((Join-Path $PWD.Path 'rp-plan.txt'), [string[]]$plan, [Text.UTF8Encoding]::new($false))
$env:NCG2_RP_PROGRAM = (Resolve-Path ./rp-plan.txt).Path
```

| ボード | Cargo の `--target` | `--features` | UF2 ファミリー |
| --- | --- | --- | --- |
| Pico | `thumbv6m-none-eabi` | `pico,spi` | `rp2040` |
| Pico 2 | `thumbv8m.main-none-eabihf` | `pico2,spi` | `rp2350-arm-s` |

Pico 2 用のビルド例を示す。`--manifest-path` は Core の配置に合わせる。Pico では表にあるターゲットと feature を指定する。

```powershell
rustup target add --toolchain 1.99.1 thumbv8m.main-none-eabihf
cargo +1.99.1 build --manifest-path ../../../circuitgame2-core/firmware/rp/Cargo.toml --locked --release --target thumbv8m.main-none-eabihf --features pico2,spi --bin ncg2-rp
```

生成した ELF を UF2 に変換し、BOOTSEL モードで起動したボードへコピーする。 [Core の UF2 変換手順](https://github.com/neknaj/circuitgame2-core/tree/main/firmware/rp#ビルド)

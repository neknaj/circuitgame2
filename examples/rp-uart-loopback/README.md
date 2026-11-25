# Pico と Pico 2 で試す UART エコー

Pico の UART0 で受信した1バイトを NCG2 回路に渡し、同じ UART0 で送り返す。通信設定は 115200 baud、8 データビット、パリティなし、1 ストップビット。

## ファームウェアを作る

[CLI をインストール](../../README.md#cli-で回路を試す)し、このディレクトリで配線表を作る。Pico を使う場合は `board.toml` の `board` を `"pico"` に変更する。回路はこのディレクトリにあるソースだけで動く。

```sh
ncg2 rp-plan --project circuitgame2.toml --board board.toml > rp-plan.txt
```

Windows PowerShell では、次の手順で配線表を UTF-8 で保存する。

```powershell
$plan = ncg2 rp-plan --project circuitgame2.toml --board board.toml
if ($LASTEXITCODE -ne 0) { throw "配線表を生成できない" }
[IO.File]::WriteAllLines((Join-Path $PWD.Path 'rp-plan.txt'), [string[]]$plan, [Text.UTF8Encoding]::new($false))
```

`NCG2_RP_PROGRAM` に配線表の絶対パスを指定し、[Core の RP ファームウェア](https://github.com/neknaj/circuitgame2-core/tree/main/firmware/rp)をビルドする。次は Pico 2 の PowerShell の例。Core の位置に合わせてマニフェストのパスを調整する。

```powershell
rustup target add --toolchain 1.99.1 thumbv8m.main-none-eabihf
$env:NCG2_RP_PROGRAM = (Resolve-Path ./rp-plan.txt).Path
cargo +1.99.1 build --manifest-path ../../../circuitgame2-core/firmware/rp/Cargo.toml --locked --release --target thumbv8m.main-none-eabihf --features pico2,uart --bin ncg2-rp
```

Pico では `thumbv6m-none-eabi` を追加してビルドのターゲットにも指定し、機能には `pico,uart` を選ぶ。生成した ELF を `elf2uf2-rs` で UF2 に変換する。次は Pico 2 の例。

```powershell
cargo install elf2uf2-rs --locked
elf2uf2-rs convert --family rp2350-arm-s ../../../circuitgame2-core/firmware/rp/target/thumbv8m.main-none-eabihf/release/ncg2-rp ncg2-rp.uf2
```

Pico では ELF のパスのターゲットを `thumbv6m-none-eabi` に、`--family` を `rp2040` に変更する。BOOTSEL ボタンを押しながらボードを USB につなぎ、表示されたドライブに UF2 をコピーする。

## 1バイト送り返す

3.3 V ロジックの USB–UART アダプターを使う。ボードの GP0 をアダプターの RX、GP1 を TX につなぎ、GND を共通にする。端末のローカルエコーとフロー制御をオフにし、改行を付けずに `H` を1バイト送る。`H` が1回返る。複数の文字を試すときは、各文字の応答を待ってから次を送る。 [ボードのピン配置](https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html)

回路は、UART が送信可能なときに受信1バイトを受け取り、その値を送信に渡す。連続した文字列を扱うには、送受信の間にバッファーが必要になる。回路が自律的に送信する波形は、[順序回路で UART 送信](../clocked-uart-transmitter/)で試せる。

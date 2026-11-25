"""NCG2 の送信波形を 8N1 の受信側で復号する。"""

import subprocess
from pathlib import Path


PROJECT = Path(__file__).with_name("circuitgame2.toml")
MESSAGE = b"Hello, world!"
PHASES = (8, *range(8), 9)


def low_bits(value, width):
    return format(value, f"0{width}b")[::-1]


def transmit(message):
    waveform = [1]
    for byte in message:
        for phase in PHASES:
            signals = low_bits(byte, 8) + low_bits(phase, 4)
            output = subprocess.check_output(
                ["ncg2", "eval", "--func", "::uart-bit", "--input", signals,
                 "--project", str(PROJECT)],
                encoding="utf-8",
            ).strip()
            if output not in ("0", "1"):
                raise ValueError(f"送信回路の出力が1ビットではない: {output!r}")
            waveform.append(int(output))
    return waveform


def receive(waveform):
    if waveform[0] != 1:
        raise ValueError("アイドル状態から始まっていない")
    position = 1
    message = bytearray()
    while position < len(waveform):
        if waveform[position] == 1:
            position += 1
            continue
        frame = waveform[position:position + 10]
        if len(frame) != 10 or frame[9] != 1:
            raise ValueError(f"フレーミングエラー: {position} ビット目")
        message.append(sum(bit << index for index, bit in enumerate(frame[1:9])))
        position += 10
    return bytes(message)


if __name__ == "__main__":
    received = receive(transmit(MESSAGE))
    if received != MESSAGE:
        raise SystemExit(f"受信内容が一致しない: {received!r}")
    print(received.decode("ascii"))

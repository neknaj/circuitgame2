"""自律送信する UART の TX 波形を検査し、受信した文字列を表示する。"""

import subprocess
from pathlib import Path


RUN_TICKS = 17_000
BIT_TICKS = 128
FRAME_BITS = 10
EXPECTED = b"Hello, world!"


def parse_trace(trace):
    """tick 0 から始まる1ビット出力を順に読み取る。"""
    levels = []
    for tick, row in enumerate(trace.splitlines()):
        fields = row.split()
        if len(fields) != 2 or fields[0] != str(tick) or fields[1] not in ("0", "1"):
            raise ValueError(f"tick {tick} の出力 {row!r} は形式が不正")
        levels.append(int(fields[1]))
    if len(levels) != RUN_TICKS + 1:
        raise ValueError(f"{RUN_TICKS + 1} 行の出力が必要")
    return levels


def receive(levels):
    """アイドル後の立ち下がりから、各ビット区間を検査して 8N1 を復号する。"""
    if levels[:2] != [0, 1]:
        raise ValueError("reset 直後に TX が High にならない")
    start = next((tick for tick in range(2, len(levels)) if levels[tick] == 0), None)
    if start is None:
        raise ValueError("開始ビットが見つからない")

    received = bytearray()
    for _ in EXPECTED:
        frame = []
        for cell in range(FRAME_BITS):
            first = start + cell * BIT_TICKS
            window = levels[first:first + BIT_TICKS]
            if len(window) != BIT_TICKS or any(level != window[0] for level in window):
                raise ValueError(f"tick {first} からの {BIT_TICKS} tick で TX が一定でない")
            frame.append(window[0])
        if frame[0] != 0 or frame[-1] != 1:
            raise ValueError(f"tick {start} からのフレームで開始または停止ビットが不正")
        received.append(sum(bit << index for index, bit in enumerate(frame[1:9])))
        start += FRAME_BITS * BIT_TICKS

    if len(levels) - start < BIT_TICKS or 0 in levels[start:]:
        raise ValueError("送信後に TX がアイドルの High を保持していない")
    if received != EXPECTED:
        raise ValueError(f"受信バイト列 {bytes(received)!r} が期待値と異なる")
    return received.decode("ascii")


def main():
    project = Path(__file__).resolve().with_name("circuitgame2.toml")
    trace = subprocess.check_output(
        ["ncg2", "run", "--project", str(project), "--ticks", str(RUN_TICKS)],
        encoding="utf-8",
    )
    print(receive(parse_trace(trace)))


if __name__ == "__main__":
    main()

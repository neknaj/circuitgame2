"""行列キー入力、NCG2 の加減算、I²C LCD への書き込みを順に模擬する。"""

import argparse
import re
import subprocess
from pathlib import Path


PROJECT = Path(__file__).with_name("circuitgame2.toml")
KEYS = ("123+", "456-", "789=", "C0  ")
SEGMENTS = {
    " ": "", "-": "g", "0": "abcdef", "1": "bc", "2": "abdeg",
    "3": "abcdg", "4": "bcfg", "5": "acdfg", "6": "acdefg",
    "7": "abc", "8": "abcdefg", "9": "abcdfg",
}
# PCF8576D 図13の静的駆動。各桁の RAM 列に MSB からこの順で書く。
SEGMENT_ORDER = "cbafgedp"
ADDRESS_WRITE = 0x38 << 1
LCD_SETUP = (0xC9, 0xE0, 0x00)


def scan_key(pressed):
    # 行を一つずつ Low にし、閉じたスイッチで Low になる列を探す。
    for active_row, row in enumerate(KEYS):
        columns = [1, 1, 1, 1]
        for switch_row, switch_column in pressed:
            if switch_row == active_row:
                columns[switch_column] = 0
        for column, level in enumerate(columns):
            if level == 0:
                return row[column]
    return None


def enter_keys(text):
    sampled = []
    for key in text:
        switches = [
            (row, col)
            for row, keys in enumerate(KEYS)
            for col, label in enumerate(keys)
            if label == key
        ]
        if len(switches) != 1:
            raise ValueError(f"キー行列にないキー: {key!r}")
        found = scan_key(switches)
        if found == "C":
            sampled.clear()
        else:
            sampled.append(found)
        if scan_key(()) is not None:
            raise ValueError("キーを離した状態を検出できない")
    return "".join(sampled)


def calculate(expression):
    match = re.fullmatch(r"([0-9]{1,2})([+-])([0-9]{1,2})=", expression)
    if match is None:
        raise ValueError("0〜99 の加減算を指定する。例: 19+23=")
    left, operator, right = match.groups()
    word = f"{int(left):08b}"[::-1] + f"{int(right):08b}"[::-1]
    word += str(int(operator == "-"))
    output = subprocess.check_output(
        ["ncg2", "eval", "--func", "::add-subtract", "--input", word, "--project", str(PROJECT)],
        encoding="utf-8",
    ).strip()
    if len(output) != 9 or any(bit not in "01" for bit in output):
        raise ValueError(f"加減算回路の出力が9ビットではない: {output!r}")
    number = int(output[:8][::-1], 2)
    return number - 256 if output[8] == "1" else number


def segment_byte(char):
    return sum(1 << (7 - index) for index, name in enumerate(SEGMENT_ORDER) if name in SEGMENTS[char])


def display_bytes(text):
    return bytes(segment_byte(char) for char in text.rjust(4))



def lcd_ack(received):
    # このモデルは指定アドレスの設定と4 桁分のデータを受け付ける。
    header = (ADDRESS_WRITE, *LCD_SETUP)
    return len(received) <= 8 and tuple(received[:4]) == header[:len(received)]


def i2c_write(data, acknowledge):
    levels = [(1, 1), (1, 0)]
    received = bytearray()

    def pulse(controller_releases, target_pulls_low=False):
        sda = int(controller_releases and not target_pulls_low)
        levels.extend(((0, sda), (1, sda)))

    for byte in data:
        for shift in range(7, -1, -1):
            pulse((byte >> shift) & 1)
        received.append(byte)
        # 9 クロック目は送信側が SDA を解放し、受信側が ACK を決める。
        accepted = acknowledge(received)
        pulse(controller_releases=True, target_pulls_low=accepted)
        if not accepted:
            break
    levels.extend(((0, 0), (1, 0), (1, 1)))
    return levels



def lcd_receive(levels):
    if levels[:2] != [(1, 1), (1, 0)] or levels[-3:] != [(0, 0), (1, 0), (1, 1)]:
        raise ValueError("I²C の START または STOP が欠けている")
    samples = [
        sda for previous, (scl, sda) in zip(levels[1:-4], levels[2:-3])
        if previous[0] == 0 and scl == 1
    ]
    if len(samples) % 9:
        raise ValueError("I²C のバイトが途中で終わった")
    received = []
    for index in range(0, len(samples), 9):
        bits = samples[index:index + 9]
        if bits[8]:
            raise ValueError("LCD が ACK を返していない")
        received.append(sum(bit << (7 - shift) for shift, bit in enumerate(bits[:8])))
    if tuple(received[:4]) != (ADDRESS_WRITE, *LCD_SETUP) or len(received) != 8:
        raise ValueError("LCD のアドレス、設定または表示データの長さが違う")
    patterns = {segment_byte(letter): letter for letter in SEGMENTS}
    return "".join(patterns[byte] for byte in received[4:]).strip(), bytes(received)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("keys", nargs="?", default="19+23=")
    args = parser.parse_args()
    try:
        expression = enter_keys(args.keys)
        result = str(calculate(expression))
        data = (ADDRESS_WRITE, *LCD_SETUP, *display_bytes(result))
        shown, wire = lcd_receive(i2c_write(data, lcd_ack))
        if shown != result:
            raise ValueError(f"LCD の表示が一致しない: {shown!r}")
    except (ValueError, KeyError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error)) from error
    print(f"{expression} {shown}")
    print(f"I2C: {wire.hex(' ')}")

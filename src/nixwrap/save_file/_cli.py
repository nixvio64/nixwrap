"""CLI: rl-decrypt -- decrypt/inspect Rocket League save files."""

import argparse
import json
import sys
from pathlib import Path

from nixwrap.save_file._file_io import parse_savedata, assemble_savedata


def main() -> None:
    p = argparse.ArgumentParser(
        description="decrypt/recrypt Rocket League SaveData files")
    p.add_argument("input", help=".save or .json file")
    p.add_argument("-o", "--output", help="Output file path")
    p.add_argument("--encrypt", action="store_true",
                   help="json -> .save (input must be .json)")
    p.add_argument("--compact", action="store_true",
                   help="minified json")
    p.add_argument("--no-crc", action="store_true",
                   help="skip crc warning")
    args = p.parse_args()

    if args.encrypt:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
        out = args.output or Path(args.input).with_suffix('.save').name
        assemble_savedata(data, out)
    else:
        result = parse_savedata(args.input, check_crc=not args.no_crc)
        indent = None if args.compact else 2
        j = json.dumps(result, indent=indent, ensure_ascii=False)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(j)
            print(f"Output written to {args.output}")
        else:
            print(j)


if __name__ == "__main__":
    main()

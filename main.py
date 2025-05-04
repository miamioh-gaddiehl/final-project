import argparse
from pathlib import Path

from app import create_app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--database", type=Path, default="./notes.db")

    args = parser.parse_args()

    app = create_app(
        database=str(Path(args.database).absolute()),
        testing=args.test,
    )

    app.run(host='0.0.0.0', debug=args.debug)


if __name__ == "__main__":
    main()

"""Manual, state-checked recovery for a source load batch."""

import argparse

from loaders.suumo_batch_loader import reset_source_batch


def main() -> None:
    """Parse operator input and reset one eligible batch."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch_id", type=int)
    parser.add_argument("--stale-minutes", type=int, default=60)
    args = parser.parse_args()
    reset_source_batch(args.batch_id, args.stale_minutes)
    print(f"Batch {args.batch_id} is pending")


if __name__ == "__main__":
    main()

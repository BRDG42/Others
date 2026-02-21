"""
Integration with Python's `antigravity` module — Google's Easter egg tribute.

The `antigravity` module is a Python Easter egg inspired by XKCD comic #353.
It also includes a geohashing implementation based on XKCD comic #426.

This script provides:
  - A geohash coordinate generator using the antigravity.geohash algorithm
  - A launcher for the classic XKCD antigravity comic
"""

import argparse
import sys


def compute_geohash(latitude, longitude, date_str):
    """Compute a geohash destination using the XKCD geohashing algorithm.

    Uses the antigravity module's built-in geohash function which implements
    the algorithm from XKCD comic #426: take your coordinates and a date's
    Dow Jones opening average to produce adventure coordinates.

    Args:
        latitude: Base latitude as a float.
        longitude: Base longitude as a float.
        date_str: Date as a string in YYYY-MM-DD format (used as the dession).

    Returns:
        The geohash object with destination coordinates.
    """
    import antigravity

    dession = date_str.encode("utf-8")
    return antigravity.geohash(latitude, longitude, dession)


def launch_comic():
    """Open the XKCD #353 antigravity comic in the default web browser.

    This is the core Easter egg: `import antigravity` opens the comic
    that shows a Python programmer discovering that importing antigravity
    lets them fly.
    """
    import antigravity  # noqa: F401 — side effect: opens browser to xkcd.com/353


def main():
    parser = argparse.ArgumentParser(
        description="Google Antigravity integration — geohashing and Easter egg launcher"
    )
    subparsers = parser.add_subparsers(dest="command")

    # Geohash subcommand
    geo_parser = subparsers.add_parser(
        "geohash",
        help="Compute geohash coordinates from a lat/lon and date",
    )
    geo_parser.add_argument("latitude", type=float, help="Base latitude")
    geo_parser.add_argument("longitude", type=float, help="Base longitude")
    geo_parser.add_argument(
        "date",
        type=str,
        help="Date string in YYYY-MM-DD format (used as dession input)",
    )

    # Comic launcher subcommand
    subparsers.add_parser(
        "fly",
        help="Open the XKCD #353 antigravity comic in your browser",
    )

    args = parser.parse_args()

    if args.command == "geohash":
        result = compute_geohash(args.latitude, args.longitude, args.date)
        print(f"Geohash result for ({args.latitude}, {args.longitude}) on {args.date}:")
        print(f"  {result}")
    elif args.command == "fly":
        print("Opening XKCD #353 — you're about to defy gravity...")
        launch_comic()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

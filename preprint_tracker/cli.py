"""Command-line interface for preprint-tracker."""
import argparse
import sys

from .core import STATUSES, PreprintLog


def main(argv=None, fetch=None):
    ap = argparse.ArgumentParser(prog="preprint-tracker", description="Track preprint versions and publication status.")
    ap.add_argument("--file", default="preprints.json")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("key", help="short name, e.g. soil-drought")
    a.add_argument("title")
    a.add_argument("--server", default="arXiv", help="arXiv, bioRxiv, medRxiv, OSF, SSRN, ...")
    a.add_argument("--id", default="", help="e.g. 2401.01234 or 10.1101/2024.01.01.123456")
    a.add_argument("--posted")
    v = sub.add_parser("version")
    v.add_argument("key")
    v.add_argument("note")
    v.add_argument("--date")
    s = sub.add_parser("status")
    s.add_argument("key")
    s.add_argument("status", choices=STATUSES)
    s.add_argument("--venue", default="")
    s.add_argument("--note", default="")
    s.add_argument("--doi", default="")
    sub.add_parser("list")
    c = sub.add_parser("changelog")
    c.add_argument("key")
    ch = sub.add_parser("check")
    ch.add_argument("key")
    sub.add_parser("attention")
    args = ap.parse_args(argv)
    log = PreprintLog(args.file)
    try:
        if args.cmd == "add":
            log.add(args.key, args.title, args.server, args.id, args.posted)
        elif args.cmd == "version":
            print("%s is now v%d" % (args.key, log.new_version(args.key, args.note, args.date)))
        elif args.cmd == "status":
            log.set_status(args.key, args.status, args.venue, args.note, args.doi)
        elif args.cmd == "list":
            for k, p in log.data.items():
                print("%-20s v%-2d %-13s %4dd  %s" % (k, p["versions"][-1]["v"], p["status"], log.days_in_status(k), p["title"][:50]))
        elif args.cmd == "changelog":
            sys.stdout.write(log.changelog(args.key))
        elif args.cmd == "check":
            remote, local = log.check_remote(args.key, **({"fetch": fetch} if fetch else {}))
            print("arXiv has v%s, log has v%d%s" % (remote, local, " - log is behind!" if remote and remote > local else ""))
            return 1 if remote and remote > local else 0
        else:
            items = log.needs_attention()
            for k, why in items:
                print("%-20s %s" % (k, why))
            if not items:
                print("nothing needs attention")
    except (KeyError, ValueError, OSError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    return 0

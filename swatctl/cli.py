import argparse
import sys
from pathlib import Path
from . import core

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    p = argparse.ArgumentParser(prog="swatctl")
    sub = p.add_subparsers(dest="cmd")

    a_create = sub.add_parser("create-project")
    a_create.add_argument("path")
    a_create.add_argument("--name", default="swat-project")
    a_create.add_argument("--swat-repo", default="https://github.com/yourorg/swat.git")
    a_create.add_argument("--ref", default=None)

    a_page = sub.add_parser("create-page")
    a_page.add_argument("project")
    a_page.add_argument("pagename")
    a_page.add_argument("--title", default=None)
    a_page.add_argument("--overwrite", action="store_true")

    a_sv = sub.add_parser("swat-set-version")
    a_sv.add_argument("project")
    a_sv.add_argument("--repo", default="https://github.com/yourorg/swat.git")
    a_sv.add_argument("--ref", required=True)
    a_sv.add_argument("--no-backup", action="store_true")

    a_pi = sub.add_parser("plugin-install")
    a_pi.add_argument("project")
    a_pi.add_argument("repo")
    a_pi.add_argument("--ref", default=None)
    a_pi.add_argument("--subpath", default=None)
    a_pi.add_argument("--overwrite", action="store_true")

    a_psv = sub.add_parser("plugin-set-version")
    a_psv.add_argument("project")
    a_psv.add_argument("plugin_name")
    a_psv.add_argument("ref")

    a_info = sub.add_parser("info")
    a_info.add_argument("project", nargs="?", default=".")

    args = p.parse_args(argv)
    try:
        if args.cmd == "create-project":
            core.create_project(Path(args.path), args.name, args.swat_repo, version=args.ref)
        elif args.cmd == "create-page":
            core.create_page(Path(args.project), args.pagename, args.title or args.pagename, overwrite=args.overwrite)
        elif args.cmd == "swat-set-version":
            core.set_swat_version(Path(args.project), args.repo, args.ref, backup=not args.no_backup)
        elif args.cmd == "plugin-install":
            core.plugin_install(Path(args.project), args.repo, ref=args.ref, plugin_subpath=args.subpath, overwrite=args.overwrite)
        elif args.cmd == "plugin-set-version":
            core.plugin_set_version(Path(args.project), args.plugin_name, args.ref)
        elif args.cmd == "info":
            info = core.show_info(Path(args.project))
            print(info)
        else:
            p.print_help()
            return 2
    except Exception as e:
        print("Error:", e, file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
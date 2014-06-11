__author__ = 'ivo'

import argparse
import logging

from blackswan import config

_log = logging.getLogger(__name__)

def list_modules(args):
    from blackswan import modules
    for name,cls in config.modules.items():
        print("{} {}".format(name.ljust(20, " "), cls.description))
    pass

def display_module(args):
    from blackswan import modules
    modcls = config.modules[args.module]
    print("{}\n{}\n\n{}".format(modcls.modname, len(modcls.modname)*"-",modcls.argparser.format_help()))

def run_module(args):
    __import__("blackswan.modules.{}".format(args.module))
    modcls = config.modules[args.module]
    modinst = modcls()
    modinst.parse_args(args.modargs)
    modinst.run()

def list_metafiles(args):
    pass

def list_indicators(args):
    pass

def db_info(args):
    pass

def main():
    parser = argparse.ArgumentParser(description="Blackswan cli")
    parser.add_argument("--debug", "-d", help="Enable debug output")

    subparsers = parser.add_subparsers(title="subcommands", description="valid subcommands", dest="cmd")
    sp_list_modules = subparsers.add_parser("list_modules", help="List all the available modules", aliases=["l"])
    sp_list_modules.set_defaults(func=list_modules)

    sp_helpmod = subparsers.add_parser("help", help="Display help for the module", aliases=["h"])
    sp_helpmod.add_argument("module", help="The module to display")
    sp_helpmod.set_defaults(func=display_module)

    sp_runmod = subparsers.add_parser("run", help="Run a module", aliases=["r"])
    sp_runmod.add_argument("module", help="The module to run")
    sp_runmod.add_argument("modargs", nargs="*", help="The module arguments. See help <modname>")
    sp_runmod.set_defaults(func=run_module)
    args = parser.parse_args()
    if args.debug:
        config.set_debug()
    if args.cmd:
        args.func(args)

if __name__ == "__main__":
    main()
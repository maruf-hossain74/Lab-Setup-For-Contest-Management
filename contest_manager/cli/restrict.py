#!/usr/bin/env python3
"""
Contest Environment Restrict CLI
"""
import sys
import argparse
from pathlib import Path

from contest_manager.utils.utils import check_root
from contest_manager.utils.internet_handler import *
from contest_manager.utils.usb_handler import *
from contest_manager.utils.persistence_handler import start_persistence

CONFIG_DIR = Path(__file__).parent.parent.parent / 'config'
BLACKLIST_TXT = CONFIG_DIR / 'blacklist.txt'

def create_parser():
    parser = argparse.ArgumentParser(
        description="Restrict contest user environment (network, USB, persistent)",
        prog="contest-restrict"
    )
    parser.add_argument(
        'user', nargs='?', default='participant', help='Username to restrict (default: participant)'
    )
    parser.add_argument(
        '--config-dir', type=str, help='Configuration directory path (default: project root)'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true', help='Enable verbose output'
    )
    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()
    check_root()
    print("\n🧹 STEP 1: Remove Previous Restrictions\n" + ("="*40))
    print("Removing internet restriction...")
    unrestrict_internet(args.user, BLACKLIST_TXT, verbose=args.verbose)
    print("Removing USB restriction...")
    unrestrict_usb_storage_device(args.user, verbose=args.verbose)
    print("✅ Previous restrictions removed.\n")

    print("\n🌐 STEP 2: Restrict Internet Access\n" + ("="*40))
    restrict_internet(args.user, BLACKLIST_TXT, verbose=args.verbose)
    print("✅ Internet access restricted.\n")

    print("\n🔌 STEP 3: Block USB Storage Devices\n" + ("="*40))
    restrict_usb_storage_device(args.user, verbose=args.verbose)
    print("✅ USB storage devices blocked.\n")

    print("\n⏰ STEP 4: Persisting Restrictions\n" + ("="*40))
    start_persistence(args.user)
    print("✅ Restrictions persisted successfully!\n")

    print("\n🎉✅ Restrictions applied successfully!")
    sys.exit(0)

if __name__ == "__main__":
    main()

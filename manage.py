#!/usr/bin/env python
"""Tien ich dong lenh cua Django (chay server, migrate, test...)."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "store_config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Chua cai Django. Hay kich hoat moi truong ao roi chay: pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

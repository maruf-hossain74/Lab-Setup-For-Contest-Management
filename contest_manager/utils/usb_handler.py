#!/usr/bin/env python3
"""
USB Device Restriction Manager
Blocks USB storage device mounting for a specific user using polkit rules.
Does not block mice or keyboards.
"""

import os

def restrict_usb_storage_device(user, verbose=False):
    """
    Restrict USB storage device mounting for the given user using polkit.
    """
    polkit_rule_path = f"/etc/polkit-1/rules.d/99-block-usb-storage-{user}.rules"
    rule = f'''
                // Block USB storage mounting for user {user}
                polkit.addRule(function(action, subject) {{
                    if (action.id == "org.freedesktop.udisks2.filesystem-mount" && subject.user == "{user}") {{
                        return polkit.Result.NO;
                    }}
                }});
            '''
    try:
        with open(polkit_rule_path, "w") as f:
            f.write(rule)
        if verbose:
            print(f"Polkit rule created: {polkit_rule_path}")
        print(f"USB storage device mounting blocked for user: {user}")
        return True
    except Exception as e:
        print(f"Failed to block USB storage for user {user}: {e}")
        return False

def unrestrict_usb_storage_device(user, verbose=False):
    """
    Remove USB storage device restriction for the given user by deleting the polkit rule.
    """
    polkit_rule_path = f"/etc/polkit-1/rules.d/99-block-usb-storage-{user}.rules"
    try:
        if os.path.exists(polkit_rule_path):
            os.remove(polkit_rule_path)
            if verbose:
                print(f"Removed polkit rule: {polkit_rule_path}")
        print(f"USB storage device mounting unblocked for user: {user}")
        return True
    except Exception as e:
        print(f"Failed to unblock USB storage for user {user}: {e}")
        return False

def usb_restriction_check(user):
    """
    Check if USB storage device restriction is applied for the given user (polkit rule exists).
    Returns True if restricted, False otherwise.
    """
    polkit_rule_path = f"/etc/polkit-1/rules.d/99-block-usb-storage-{user}.rules"
    return os.path.exists(polkit_rule_path)
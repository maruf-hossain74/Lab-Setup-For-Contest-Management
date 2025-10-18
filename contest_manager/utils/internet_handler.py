"""
Internet restriction utilities for contest-manager
"""

import pwd
import json
import shlex
import subprocess
import dns.resolver
from pathlib import Path

def get_user_cache_path(user):
    """Return the cache path for a user."""
    cache_dir = Path(__file__).parent.parent.parent / 'cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"ip_cache_{user}.json"

def get_targets_from_blacklist(blacklist_path):
    """Read blacklist, filter domains, and generate targets."""
    if not Path(blacklist_path).exists():
        print(f"❌ Blacklist file {blacklist_path} not found.")
        return []
    domains = []
    with open(blacklist_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                domains.append(line)
    if not domains:
        print("⚠️  No domains found in blacklist. Skipping IP cache.")
        return []
    allow_patterns = ['static.', 'cdn.', 'fonts.']
    targets = []
    for domain in domains:
        if any(domain.startswith(p) for p in allow_patterns):
            continue
        targets.append(domain)
        targets.extend(get_subdomains(domain))
    return targets

def resolve_targets_to_ip_map(targets, existing_ip_map=None):
    """Resolve IPs for each target, optionally merging with an existing map."""
    ip_map = existing_ip_map if existing_ip_map else {}
    for target in targets:
        new_ips = set(resolve_ips(target))
        old_ips = set(ip_map.get(target, []))
        ip_map[target] = list(old_ips.union(new_ips))
    return ip_map

def get_subdomains(domain):
    """Generate common subdomain names for a domain."""
    common_subs = ["www", "mail", "drive", "chat", "api", "blog", "m", "app", "cdn", "static", "dev", "test"]
    return [f"{sub}.{domain}" for sub in common_subs]

def resolve_ips(domain):
    """Resolve all IPv4 and IPv6 addresses for a domain and its subdomains."""
    ips = set()
    try:
        answers = dns.resolver.resolve(domain, 'A')
        for rdata in answers:
            ips.add(str(rdata))
    except Exception:
        pass
    try:
        answers = dns.resolver.resolve(domain, 'AAAA')
        for rdata in answers:
            ips.add(str(rdata))
    except Exception:
        pass
    return ips

def update_ip_cache(user, blacklist_path, verbose=False):
    """
    Update the stored IP cache for the user by merging new IPs for all domains and subdomains.
    Preserves old entries and adds new ones.
    """
    cache_path = get_user_cache_path(user)
    if verbose:
        print(f"[update_ip_cache] Updating IP cache from {blacklist_path} to {cache_path}")
    ip_map = {}
    if cache_path.exists():
        with open(cache_path) as f:
            try:
                ip_map = json.load(f)
            except Exception:
                ip_map = {}
    targets = get_targets_from_blacklist(blacklist_path)
    if not targets:
        return False, None
    ip_map = resolve_targets_to_ip_map(targets, ip_map)
    with open(cache_path, 'w') as f:
        json.dump(ip_map, f, indent=2)
    if verbose:
        print(f"IP cache updated and saved to {cache_path}")
    return True, str(cache_path)

def create_ip_cache(user, blacklist_path, verbose=False):
    """
    Create a fresh IP cache for the user. Overwrites any previous cache.
    """
    cache_path = get_user_cache_path(user)
    if verbose:
        print(f"[create_ip_cache] Reading blacklist from {blacklist_path}")
    targets = get_targets_from_blacklist(blacklist_path)
    if not targets:
        return False, None
    ip_map = resolve_targets_to_ip_map(targets)
    with open(cache_path, 'w') as f:
        json.dump(ip_map, f, indent=2)
    if verbose:
        print(f"IP cache created at {cache_path}")
    return True, str(cache_path)

def apply_restrictions_from_cache(user, verbose=False):
    """
    Apply iptables/ip6tables rules for all cached IPs for the user.
    """
    cache_path = get_user_cache_path(user)
    if not Path(cache_path).exists():
        print(f"❌ IP cache file {cache_path} not found.")
        return False
    try:
        uid = pwd.getpwnam(user).pw_uid
    except Exception:
        print(f"❌ User {user} not found.")
        return False
    with open(cache_path) as f:
        ip_map = json.load(f)
    for target, ips in ip_map.items():
        for ip in ips:
            try:
                if ':' in ip:
                    subprocess.run(["ip6tables", "-A", "OUTPUT", "-d", ip, "-m", "owner", "--uid-owner", str(uid), "-j", "DROP"], check=True)
                else:
                    subprocess.run(["iptables", "-A", "OUTPUT", "-d", ip, "-m", "owner", "--uid-owner", str(uid), "-j", "DROP"], check=True)
            except Exception:
                pass
        # Block DNS requests for the domain/subdomain
        try:
            subprocess.run(["iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "53", "-m", "string", "--string", target, "--algo", "bm", "-m", "owner", "--uid-owner", str(uid), "-j", "DROP"], check=True)
        except Exception:
            pass
        # Block DNS over HTTPS (DoH) for the domain/subdomain (TCP 443)
        try:
            subprocess.run(["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "443", "-m", "string", "--string", target, "--algo", "bm", "-m", "owner", "--uid-owner", str(uid), "-j", "DROP"], check=True)
            subprocess.run(["ip6tables", "-A", "OUTPUT", "-p", "tcp", "--dport", "443", "-m", "string", "--string", target, "--algo", "bm", "-m", "owner", "--uid-owner", str(uid), "-j", "DROP"], check=True)
        except Exception:
            pass
    if verbose:
        print(f"Applied restrictions for user {user} from cache {cache_path}")
    print("✅ Internet restrictions applied for user from cache.")
    return True

def restrict_internet(user, blacklist_path, verbose=False):
    """
    Restrict internet access for the given user based on blacklist file.
    Uses create_ip_cache and apply_restrictions_from_cache.
    """
    success, _ = create_ip_cache(user, blacklist_path, verbose=verbose)
    if not success:
        print("Failed to create IP cache. No restrictions applied.")
        return False
    return apply_restrictions_from_cache(user, verbose=verbose)

def unrestrict_internet(user, blacklist_path, verbose=False):
    """
    Remove all iptables/ip6tables OUTPUT rules for the given user UID.
    This flushes any network restrictions for the user, regardless of origin or type.
    """
    print(f"🔓 Flushing all iptables/ip6tables OUTPUT rules for user: {user}")
    try:
        uid = pwd.getpwnam(user).pw_uid
    except Exception:
        print(f"❌ User {user} not found.")
        return
    tables = ["iptables", "ip6tables"]
    for table in tables:
        # List all rules in OUTPUT chain
        result = subprocess.run([table, "-L", "OUTPUT", "--line-numbers", "-n", "-v"], capture_output=True, text=True)
        lines = result.stdout.splitlines()
        # Find line numbers for rules with --uid-owner <uid>
        rule_lines = []
        for line in lines:
            if f"--uid-owner {uid}" in line:
                parts = line.strip().split()
                if parts and parts[0].isdigit():
                    rule_lines.append(int(parts[0]))
        # Delete rules from bottom to top
        for line_num in sorted(rule_lines, reverse=True):
            del_cmd = [table, "-D", "OUTPUT", str(line_num)]
            del_result = subprocess.run(del_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if del_result.returncode == 0:
                print(f"[{table}] Deleted OUTPUT rule at line {line_num} for UID {uid}")
        if not rule_lines:
            print(f"[{table}] No OUTPUT rules for UID {uid} found.")
    print(f"✅ All iptables/ip6tables OUTPUT rules for user UID {uid} fully removed.")


def internet_restriction_check(user):
    """
    Check if internet restriction is applied for the given user (any iptables/ip6tables OUTPUT DROP rules for UID).
    Returns True if any such rule exists, False otherwise.
    """
    try:
        uid = pwd.getpwnam(user).pw_uid
    except Exception:
        print(f"❌ User {user} not found.")
        return False
    for table in ["iptables", "ip6tables"]:
        try:
            result = subprocess.run([table, "-S", "OUTPUT"], capture_output=True, text=True)
            rules = result.stdout.splitlines()
            for rule in rules:
                if f"-m owner --uid-owner {uid}" in rule and "-j DROP" in rule:
                    return True
        except Exception:
            pass
    return False
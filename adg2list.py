import argparse
import re
import sys

# A simple domain token regex: requires at least one dot and allowed chars
DOMAIN_RE = re.compile(r"^(?:\*\.)?(?:[A-Za-z0-9-]{1,63}\.)+[A-Za-z]{2,63}$")
# IP-like token regex (to avoid picking up IPs)
IP_RE = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$|^\[[0-9a-fA-F:]+\]$|^[0-9a-fA-F:]+$")

# Common names to skip
SKIP_NAMES = {
    "localhost",
    "localhost.localdomain",
    "local",
    "broadcasthost",
    "ip6-localhost",
    "ip6-loopback",
    "ip6-localnet",
    "ip6-mcastprefix",
    "ip6-allnodes",
    "ip6-allrouters",
    "ip6-allhosts",
    "0.0.0.0",
}


def is_domain_token(token: str) -> bool:
    token = token.strip().lower()
    if not token:
        return False
    if token in SKIP_NAMES:
        return False
    # strip surrounding brackets (some IPv6 forms)
    if IP_RE.match(token):
        return False
    # if it contains at least one dot and matches DOMAIN_RE, accept
    if "." in token and DOMAIN_RE.match(token):
        return True
    # fallback: if contains a dot but doesn't look like an IP, accept
    if "." in token and not any(c.isspace() for c in token) and not token[0].isdigit():
        return True
    return False


def parse_hosts(stream):
    seen = {}
    for raw in stream:
        line = raw.strip()
        if not line:
            continue
        # remove inline comments starting with '#'
        if "#" in line:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
        parts = line.split()
        if not parts:
            continue
        # parts[0] may be an IP or a domain; check all tokens after removing IP-like tokens
        for token in parts:
            token = token.strip()
            if not token:
                continue
            # skip tokens that look like IPs or are the canonical IP field
            if IP_RE.match(token):
                continue
            # skip leading host-file indicator like '0.0.0.0' or '127.0.0.1'
            if token in ("0.0.0.0", "127.0.0.1", "::1"):
                continue
            # token may be something like '0.0.0.0' or 'example.com'; test
            if is_domain_token(token):
                # strip possible leading '*.' wildcard
                token = token.lstrip('*.')
                if token not in seen:
                    seen[token] = None
        # continue with next line
    return list(seen.keys())


def main():
    p = argparse.ArgumentParser(description="Convert hosts file to simple domain list")
    p.add_argument('-i', '--input', help='input hosts file (default: stdin)', default='-')
    p.add_argument('-o', '--output', help='output file (default: stdout)', default='-')
    p.add_argument('--sort', help='sort the resulting domains alphabetically', action='store_true')
    args = p.parse_args()

    if args.input == '-':
        infile = sys.stdin
    else:
        infile = open(args.input, 'r', encoding='utf-8', errors='ignore')

    domains = parse_hosts(infile)

    if args.input != '-':
        infile.close()

    if args.sort:
        domains = sorted(domains)

    if args.output == '-':
        out = sys.stdout
        for d in domains:
            out.write(d + '\n')
    else:
        with open(args.output, 'w', encoding='utf-8') as f:
            for d in domains:
                f.write(d + '\n')


if __name__ == '__main__':
    main()

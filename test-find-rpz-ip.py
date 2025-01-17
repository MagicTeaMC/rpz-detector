import dns.resolver
import dns.query
import dns.zone

"""
This is a experimental scripts made for discover more method to check if the domain is blocked by RPZ, and the script 
check if it include somethings in additional section and not a knew IP usually use by RPZ.
"""

def find_domains_with_additional_section(domains_file, dns_server, target_ip):
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dns_server]

    output_file = "rpz-ip-find.txt"
    with open(domains_file, "r") as f, open(output_file, "w") as out_f:
        for domain in f:
            domain = domain.strip()
            try:
                a_records = resolver.resolve(domain, 'A')
                domain_ips = [str(rdata) for rdata in a_records]

                try:
                    response = dns.query.udp(dns.message.make_query(domain, dns.rdatatype.A), dns_server, timeout=5)
                    if response.additional:
                        has_additional = True
                        additional_ips = []
                        for rrset in response.additional:
                            for rr in rrset:
                                if rr.rdtype == dns.rdatatype.A:
                                    additional_ips.append(str(rr))

                        if not any(ip == target_ip for ip in additional_ips) and target_ip not in domain_ips :
                           out_f.write(f"{domain}\n")
                           print(f"Found: {domain} - A records: {domain_ips}, Additional IPs: {additional_ips}")

                    else:
                        has_additional = False

                except (dns.exception.Timeout, dns.exception.DNSException):
                    print(f"Error querying additional section for {domain}: Timeout or other DNS error")

            except dns.resolver.NXDOMAIN:
                print(f"Domain not found: {domain}")
            except dns.resolver.NoAnswer:
                print(f"No A record found for: {domain}")
            except dns.exception.DNSException as e:
                print(f"Error resolving {domain}: {e}")

    return output_file

if __name__ == "__main__":
    domains_file = "domains.txt"
    dns_server = "101.101.101.101"
    target_ip = "182.173.0.181"

    output_file_path = find_domains_with_additional_section(domains_file, dns_server, target_ip)
    print(f"Results written to: {output_file_path}")
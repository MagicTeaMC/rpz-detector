import dns.resolver
import time
from threading import Timer

def query_domains(input_file, output_file, dns_server, keywords, retry_delay, max_retries):
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dns_server]
    resolver.timeout = 5
    resolver.lifetime = 10

    with open(input_file, 'r') as f:
        domains = [line.strip() for line in f if line.strip()]

    matching_domains = set()
    total_domains = len(domains)

    processed_count = 0
    start_time = time.time()
    timer_active = True

    def show_rate():
        if timer_active:
            elapsed_time = time.time() - start_time
            rate = processed_count / elapsed_time if elapsed_time > 0 else 0
            print(f"[Rate] Processed {processed_count} domains in {elapsed_time:.2f} seconds. {rate:.2f} domains/sec")
            Timer(1, show_rate).start()  # Schedule the next update

    show_rate()  # Start the rate display loop

    for index, domain in enumerate(domains, start=1):
        success = False
        attempts = 0

        while not success and attempts < max_retries:  # Add a condition to limit retries
            attempts += 1
            try:
                response = resolver.resolve(domain, 'A', raise_on_no_answer=False)

                if response.response and response.response.additional:
                    if any(keyword in str(record) for record in response.response.additional for keyword in keywords):
                        if domain not in matching_domains:
                            matching_domains.add(domain)
                            print(f"[Found] Domain: {domain}, Match #{len(matching_domains)}, Checked: {index}/{total_domains}")
                        success = True
                        break
                success = True
            except dns.resolver.NoAnswer:
                print(f"[No Answer] Domain: {domain}, Checked: {index}/{total_domains}")
                success = True
            except dns.resolver.NXDOMAIN:
                print(f"[NXDOMAIN] Domain: {domain}, Checked: {index}/{total_domains}")
                success = True
            except dns.resolver.Timeout:
                print(f"[Timeout] Retrying domain: {domain} (Attempt {attempts})")
                if attempts < max_retries:
                  time.sleep(retry_delay)
                else:
                  print(f"[Timeout] Max retries reached for domain: {domain}, Checked: {index}/{total_domains}. Skipping...")
                  success = True  # Set success to True to break the loop after max retries
            except dns.exception.DNSException as e:
                print(f"[Error] Failed to query domain: {domain}, Error: {e}, Checked: {index}/{total_domains}")
                success = True

        processed_count += 1

    # Stop the rate display loop
    timer_active = False

    with open(output_file, 'w') as f:
        f.writelines(f"{domain}\n" for domain in sorted(matching_domains))

    elapsed_time = time.time() - start_time
    final_rate = processed_count / elapsed_time if elapsed_time > 0 else 0
    print(f"Done! Total matches found: {len(matching_domains)}")
    print(f"Final rate: {final_rate:.2f} domains/sec")

# config
input_file = 'domains.txt'
output_file = 'matching_domains.txt'
dns_server = '101.101.101.101'
keywords = ['rpztw', 'rpz']
retry_delay=5
max_retries=3

query_domains(input_file, output_file, dns_server, keywords, retry_delay, max_retries)
import asyncio
import aiodns
import time
import socket

async def query_domain_async(sem, resolver_map, domain, target_ips, matching_domains, processed_count, total_domains, retry_delay, max_retries, output_file, write_counter, write_threshold, resolver_timeouts):
    async with sem:  # Acquire semaphore
        attempts = 0
        resolver_index = hash(domain) % len(resolver_map)
        resolver = resolver_map[resolver_index]

        while attempts < max_retries:
            attempts += 1
            try:
                # Set a timeout for the DNS query
                response = await asyncio.wait_for(resolver.query(domain, 'A'), timeout=resolver.timeout)

                if response:
                    for record in response:
                        ip = str(record.host)
                        if ip in target_ips:
                            matching_domains.add(domain)
                            processed_count[0] += 1
                            print(f"[Found] Domain: {domain} (Resolver {resolver_index+1}) connected to {ip}, Match #{len(matching_domains)}, Checked: {processed_count[0]}/{total_domains}")
                            write_counter[0] += 1
                            if write_counter[0] >= write_threshold:
                                await write_to_file_async(output_file, matching_domains, write_counter)  # Use async write
                            return
                processed_count[0] += 1
                return

            except aiodns.error.DNSError as e:
                error_code = e.args[0]
                if error_code == aiodns.error.ARES_ENOTFOUND:
                    print(f"[NXDOMAIN] Domain: {domain} (Resolver {resolver_index+1}), Checked: {processed_count[0]}/{total_domains}")
                elif error_code == aiodns.error.ARES_ETIMEOUT:
                    resolver_timeouts[resolver_index] += 1
                    print(f"[Timeout] Retrying domain: {domain} (Resolver {resolver_index+1}) (Attempt {attempts})")
                    if attempts < max_retries:
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        print(f"[Timeout] Max retries reached for domain: {domain} (Resolver {resolver_index+1}), Checked: {processed_count[0]}/{total_domains}. Skipping...")
                else:
                    print(f"[Error] Failed to query domain: {domain} (Resolver {resolver_index+1}), Error: {e}, Checked: {processed_count[0]}/{total_domains}")
                processed_count[0] += 1
                return

            except asyncio.TimeoutError:
                resolver_timeouts[resolver_index] += 1
                print(f"[Timeout] Retrying domain: {domain} (Resolver {resolver_index+1}) (Attempt {attempts})")
                if attempts < max_retries:
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    print(f"[Timeout] Max retries reached for domain: {domain} (Resolver {resolver_index+1}), Checked: {processed_count[0]}/{total_domains}. Skipping...")
                processed_count[0] += 1
                return

async def write_to_file_async(output_file, matching_domains, write_counter):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, write_to_file, output_file, matching_domains, write_counter)

def write_to_file(output_file, matching_domains, write_counter):
    with open(output_file, 'w') as f:
        f.writelines(f"{domain}\n" for domain in sorted(matching_domains))
    write_counter[0] = 0
    print(f"[Info] Written {len(matching_domains)} domains to {output_file}")

async def worker_async(sem, domains, resolver_map, target_ips, matching_domains, processed_count, total_domains, retry_delay, max_retries, output_file, write_counter, write_threshold, resolver_timeouts):
    for domain in domains:
        await query_domain_async(sem, resolver_map, domain, target_ips, matching_domains, processed_count, total_domains, retry_delay, max_retries, output_file, write_counter, write_threshold, resolver_timeouts)

async def query_domains_async(input_file, output_file, dns_servers, target_ips, retry_delay, max_retries, num_tasks):
    loop = asyncio.get_running_loop()

    # Create multiple resolvers
    resolver_map = []
    for dns_server in dns_servers:
        resolver = aiodns.DNSResolver(loop=loop)
        resolver.nameservers = [dns_server]
        resolver.timeout = 5
        resolver_map.append(resolver)

    with open(input_file, 'r') as f:
        domains = [line.strip() for line in f if line.strip()]

    matching_domains = set()
    total_domains = len(domains)
    processed_count = [0]
    write_counter = [0]
    write_threshold = 100
    resolver_timeouts = [0] * len(resolver_map)
    start_time = time.time()

    sem = asyncio.Semaphore(num_tasks)

    def show_rate():
        current_processed_count = processed_count[0]
        elapsed_time = time.time() - start_time
        rate = current_processed_count / elapsed_time if elapsed_time > 0 else 0
        print(f"[Rate] Processed {current_processed_count} domains in {elapsed_time:.2f} seconds. {rate:.2f} domains/sec")
        for i, timeout_count in enumerate(resolver_timeouts):
            print(f"[Resolver {i+1} Timeout Count]: {timeout_count}")

    # No need for chunking with Semaphore
    tasks = [worker_async(sem, domains, resolver_map, target_ips, matching_domains, processed_count, total_domains, retry_delay, max_retries, output_file, write_counter, write_threshold, resolver_timeouts)]

    await asyncio.gather(*tasks)

    show_rate()

    # Write any remaining domains
    if write_counter[0] > 0:
        await write_to_file_async(output_file, matching_domains, write_counter)

    elapsed_time = time.time() - start_time
    final_rate = processed_count[0] / elapsed_time if elapsed_time > 0 else 0
    print(f"Done! Total matches found: {len(matching_domains)}")
    print(f"Final rate: {final_rate:.2f} domains/sec")

if __name__ == "__main__":
    input_file = 'domains.txt'
    output_file = 'matching_domains.txt'
    dns_servers = ['101.101.101.101', '168.95.1.1', '61.31.233.1', '203.133.1.7']
    target_ips = {'182.173.0.181'}
    retry_delay = 1
    max_retries = 3
    num_tasks = 50

    asyncio.run(query_domains_async(input_file, output_file, dns_servers, target_ips, retry_delay, max_retries, num_tasks))
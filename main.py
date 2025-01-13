import dns.resolver
import time
from threading import Timer, Thread, Lock
import queue

def query_domain(resolver, domain, keywords, matching_domains, processed_count, total_domains, lock, retry_delay, max_retries):
    success = False
    attempts = 0

    while not success and attempts < max_retries:
        attempts += 1
        try:
            response = resolver.resolve(domain, 'A', raise_on_no_answer=False)

            if response.response and response.response.additional:
                if any(keyword in str(record) for record in response.response.additional for keyword in keywords):
                    with lock:
                        if domain not in matching_domains:
                            matching_domains.add(domain)
                            processed_count[0] += 1
                            print(f"[Found] Domain: {domain}, Match #{len(matching_domains)}, Checked: {processed_count[0]}/{total_domains}")
                        else:
                            processed_count[0] += 1
                    success = True
                    break
            
            with lock:
                processed_count[0] += 1
            success = True
        except dns.resolver.NoAnswer:
            with lock:
                processed_count[0] += 1
                print(f"[No Answer] Domain: {domain}, Checked: {processed_count[0]}/{total_domains}")
            success = True
        except dns.resolver.NXDOMAIN:
            with lock:
                processed_count[0] += 1
                print(f"[NXDOMAIN] Domain: {domain}, Checked: {processed_count[0]}/{total_domains}")
            success = True
        except dns.resolver.Timeout:
            print(f"[Timeout] Retrying domain: {domain} (Attempt {attempts})")
            if attempts < max_retries:
                time.sleep(retry_delay)
            else:
                with lock:
                    processed_count[0] += 1
                    print(f"[Timeout] Max retries reached for domain: {domain}, Checked: {processed_count[0]}/{total_domains}. Skipping...")
                success = True
        except dns.exception.DNSException as e:
            with lock:
                processed_count[0] += 1
                print(f"[Error] Failed to query domain: {domain}, Error: {e}, Checked: {processed_count[0]}/{total_domains}")
            success = True

def worker(q, resolver, keywords, matching_domains, processed_count, total_domains, lock, retry_delay, max_retries):
    while True:
        domain = q.get()
        if domain is None:
            break
        query_domain(resolver, domain, keywords, matching_domains, processed_count, total_domains, lock, retry_delay, max_retries)
        q.task_done()

def query_domains(input_file, output_file, dns_server, keywords, retry_delay, max_retries, num_threads):
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dns_server]
    resolver.timeout = 5
    resolver.lifetime = 10

    with open(input_file, 'r') as f:
        domains = [line.strip() for line in f if line.strip()]

    matching_domains = set()
    total_domains = len(domains)

    processed_count = [0]
    start_time = time.time()
    timer_active = True
    lock = Lock()

    def show_rate():
        if timer_active:
            with lock:
                current_processed_count = processed_count[0]
            elapsed_time = time.time() - start_time
            rate = current_processed_count / elapsed_time if elapsed_time > 0 else 0
            print(f"[Rate] Processed {current_processed_count} domains in {elapsed_time:.2f} seconds. {rate:.2f} domains/sec")
            Timer(1, show_rate).start()

    show_rate()

    q = queue.Queue()
    threads = []
    for _ in range(num_threads):
        t = Thread(target=worker, args=(q, resolver, keywords, matching_domains, processed_count, total_domains, lock, retry_delay, max_retries))
        t.start()
        threads.append(t)

    for domain in domains:
        q.put(domain)

    q.join()

    # Stop the rate display loop
    timer_active = False

    # Stop workers
    for _ in range(num_threads):
        q.put(None)
    for t in threads:
        t.join()

    with open(output_file, 'w') as f:
        f.writelines(f"{domain}\n" for domain in sorted(matching_domains))

    elapsed_time = time.time() - start_time
    with lock:
        final_rate = processed_count[0] / elapsed_time if elapsed_time > 0 else 0
    print(f"Done! Total matches found: {len(matching_domains)}")
    print(f"Final rate: {final_rate:.2f} domains/sec")

# config
input_file = 'domains.txt'
output_file = 'matching_domains.txt'
dns_server = '101.101.101.101'
keywords = ['rpztw', 'rpz']
retry_delay = 1
max_retries = 1
num_threads = 10

query_domains(input_file, output_file, dns_server, keywords, retry_delay, max_retries, num_threads)
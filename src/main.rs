use async_std::{
    fs::File,
    io::{prelude::*, BufWriter},
    sync::{Arc, Mutex},
    task,
};
use fasthash::city;
use futures::future::join_all;
use std::{
    collections::HashSet,
    hash::Hasher,
    net::IpAddr,
    time::{Duration, Instant},
};
use hickory_resolver::{
    config::{NameServerConfig, Protocol, ResolverConfig, ResolverOpts},
    error::ResolveError,
    AsyncResolver,
    TokioAsyncResolver,
    lookup_ip::LookupIpIter,
    proto::rr::RecordType,
};

// config
const DEFAULT_INPUT_FILE: &str = "domains.txt";
const DEFAULT_OUTPUT_FILE: &str = "matching_domains.txt";
const DNS_SERVERS: &[&str] = &[
    "101.101.101.101",
    "168.95.1.1",
    "168.95.192.1",
    "61.31.233.1",
    "203.133.1.7",
    "203.133.1.6",
    "210.243.121.155",
];
const TARGET_IPS: &[&str] = &["182.173.0.181"];
const RETRY_DELAY: Duration = Duration::from_millis(500);
const MAX_RETRIES: u32 = 2;
const NUM_TASKS: usize = 50;
const WRITE_THRESHOLD: usize = 100;
const RESOLVER_TIMEOUT: u64 = 5;

#[async_std::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let input_file = std::env::args().nth(1).unwrap_or_else(|| DEFAULT_INPUT_FILE.to_string());
    let output_file = std::env::args().nth(2).unwrap_or_else(|| DEFAULT_OUTPUT_FILE.to_string());

    let domains = read_domains(&input_file).await?;
    let num_domains = domains.len();

    let resolvers = create_resolvers().await?;
    let resolver_timeouts = Arc::new(
        resolvers
            .iter()
            .map(|_| Mutex::new(0_u32))
            .collect::<Vec<_>>(),
    );

    let matching_domains = Arc::new(Mutex::new(HashSet::new()));
    let processed_count = Arc::new(Mutex::new(0_usize));
    let start_time = Instant::now();

    // Rate monitoring task
    let rate_monitor_handle = task::spawn({
        let processed_count = Arc::clone(&processed_count);
        async move {
            let mut last_count = 0;
            loop {
                task::sleep(Duration::from_secs(1)).await;
                let current_count = *processed_count.lock().await;
                let rate = current_count - last_count;
                last_count = current_count;
                println!("Current rate: {} domains/sec", rate);
            }
        }
    });

    let mut tasks = Vec::new();
    for domain in domains {
        let resolvers = Arc::clone(&resolvers);
        let resolver_timeouts = Arc::clone(&resolver_timeouts);
        let matching_domains = Arc::clone(&matching_domains);
        let processed_count = Arc::clone(&processed_count);

        let task = task::spawn(async move {
            let resolver_index = {
                let mut hasher = city::Hasher64::new();
                hasher.write(domain.as_bytes());
                (hasher.finish() % resolvers.len() as u64) as usize
            };
            let resolver = &resolvers[resolver_index];
            let resolver_timeout = &resolver_timeouts[resolver_index];

            for _ in 0..=MAX_RETRIES {
                match resolver.lookup_ip(domain.as_str()).await {
                    Ok(response) => {
                        for ip in response {
                            let ip_str = ip.to_string();
                            if TARGET_IPS.contains(&ip_str.as_str()) {
                                let mut locked_matching_domains = matching_domains.lock().await;
                                locked_matching_domains.insert(domain.clone());
                                let matching_count = locked_matching_domains.len();
                                let processed = *processed_count.lock().await;
                                let elapsed = start_time.elapsed().as_secs_f64();
                                let rate = if elapsed > 0.0 {
                                    processed as f64 / elapsed
                                } else {
                                    0.0
                                };

                                println!(
                                    "Domain: {}, IP: {}, Matching: {}, Processed: {}, Rate: {:.2}/sec",
                                    domain, ip_str, matching_count, processed, rate
                                );

                                if matching_count >= WRITE_THRESHOLD {
                                    let domains_to_write: Vec<_> =
                                        locked_matching_domains.drain().collect();
                                    drop(locked_matching_domains);
                                    write_domains(&output_file, &domains_to_write).await.unwrap();
                                }
                                break;
                            }
                        }
                        break;
                    }
                    Err(err) => match err {
                            
                        ResolveError::NoRecordsFound { .. } => {
                            println!("Domain {} does not exist (NXDOMAIN or NoRecordsFound)", domain);
                            break;
                        },
                        ResolveError::Timeout { .. }=> {
                            let mut locked_timeout = resolver_timeout.lock().await;
                            *locked_timeout += 1;
                            println!(
                                "Domain {} timed out, retrying in {:?} (resolver timeout count: {})",
                                domain, RETRY_DELAY, locked_timeout
                            );
                            task::sleep(RETRY_DELAY).await;
                        },
                        _ => {
                            println!("Error querying domain {}: {:?}", domain, err);
                            break;
                        }
                    },
                }
            }

            let mut locked_processed_count = processed_count.lock().await;
            *locked_processed_count += 1;
        });

        tasks.push(task);

        if tasks.len() >= NUM_TASKS {
            join_all(tasks.drain(..)).await;
        }
    }

    join_all(tasks).await;
    rate_monitor_handle.cancel().await;

    // Write remaining domains
    let remaining_domains: Vec<_> = matching_domains.lock().await.drain().collect();
    if !remaining_domains.is_empty() {
        write_domains(&output_file, &remaining_domains).await?;
    }

    let elapsed = start_time.elapsed();
    let rate = num_domains as f64 / elapsed.as_secs_f64();
    println!(
        "Found {} matching domains out of {} in {:.2?} ({:.2}/sec)",
        remaining_domains.len(),
        num_domains,
        elapsed,
        rate
    );

    for (i, timeout_count) in resolver_timeouts.iter().enumerate() {
        println!(
            "Resolver {}: {} timeouts",
            i,
            timeout_count.lock().await
        );
    }

    Ok(())
}

async fn read_domains(filename: &str) -> Result<Vec<String>, std::io::Error> {
    let file = File::open(filename).await?;
    let reader = std::io::BufReader::new(file);
    let mut lines = reader.lines();
    let mut domains = Vec::new();

    while let Some(line) = lines.next().await {
        let domain = line?.trim().to_string();
        if !domain.is_empty() {
            domains.push(domain);
        }
    }

    Ok(domains)
}

async fn write_domains(filename: &str, domains: &[String]) -> Result<(), std::io::Error> {
    let file = File::create(filename).await?;
    let mut writer = BufWriter::new(file);

    for domain in domains {
        writer.write_all(domain.as_bytes()).await?;
        writer.write_all(b"\n").await?;
    }

    writer.flush().await?;
    Ok(())
}

async fn create_resolvers() -> Result<Vec<TokioAsyncResolver>, std::io::Error> {
    let mut resolvers = Vec::new();
    for &server in DNS_SERVERS {
        let socket_addr = format!("{}:53", server).parse().map_err(|e| {
            std::io::Error::new(
                std::io::ErrorKind::Other,
                format!("Invalid DNS server address: {}", e),
            )
        })?;

        let mut resolver_config = ResolverConfig::new();
        resolver_config.add_name_server(NameServerConfig {
            socket_addr,
            protocol: Protocol::Udp,
            tls_dns_name: None,
            trust_negative_responses: false,
            bind_addr: None,
        });

        let mut resolver_opts = ResolverOpts::default();
        resolver_opts.timeout = Duration::from_secs(RESOLVER_TIMEOUT);
        resolver_opts.num_concurrent_reqs = 0;
        let resolver = TokioAsyncResolver::tokio(resolver_config, resolver_opts).map_err(|e| {
            std::io::Error::new(
                std::io::ErrorKind::Other,
                format!("Failed to create resolver: {}", e),
            )
        })?;

        resolvers.push(resolver);
    }
    Ok(resolvers)
}
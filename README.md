# RPZ Detector
A public TWNIC's RPZ block list for everyone, open forever.  
## Purpose and Background
### RPZ Controversy
TL;DR: Taiwan's website blocking system, especially "RPZ 1.5" is controversial. It allows quick blocking without court approval, lacks transparency, and has a history of errors (it used to block some popular domains such as eu.org, Polymarket.com and Instagram.com), raising concerns about potential abuse and the restriction of digital rights. The new law further legitimizes this process, sparking fears of unchecked government power online.
#### More Info About It:
- <https://blog.ocf.tw/2024/10/ocf_14.html> ([Wayback machine](https://web.archive.org/web/2/https://blog.ocf.tw/2024/10/ocf_14.html))
- <https://www.facebook.com/seadog007/posts/pfbid02K7KwLyrchHEoWEVbG4bxQCxnLq81Dj6f4ig9Qt5nbGWsgj3zsfXqc9EATgvwo8CUl> ([Wayback machine](https://web.archive.org/web/20230607001325/https://www.facebook.com/seadog007/posts/pfbid02K7KwLyrchHEoWEVbG4bxQCxnLq81Dj6f4ig9Qt5nbGWsgj3zsfXqc9EATgvwo8CUl))
## Download RPZ Block List
> This list is not complete, RPZ blocked more than just these domains. Counting only 2024, RPZ has blocked [at least 30,000 domains.](https://rpz.twnic.tw/e_2.html).  

[rpz-block-list.txt](https://github.com/MagicTeaMC/rpz-detector/blob/main/rpz-block-list.txt)  
This block list can be use at anywhere for any legal purpose.  
## Start Using
### Python Script
1. Create a venv and install requirements.
2. Clone domains list [here](https://github.com/tb0hdan/domains), and merge it with `merge_datas.py`, or use other source  
3. Check if the domains is still alive with [massdns](https://github.com/blechschmidt/massdns) (optional)
4. Config to your want in `main.py` (optional)
5. Run `main.py` then waiting for a while (maybe a day or so)
### Rust Script (Beta)
2. Clone domains list [here](https://github.com/tb0hdan/domains), and merge it with `merge_datas.py`, or use other source 
3. Check if the domains is still alive with [massdns](https://github.com/blechschmidt/massdns) (optional)
4. Config to your want in `src/main.rs` (optional)
1. Use `cargo build --release` to build a executable file.
5. Run executable file then waiting for a while.
### MassDNS (Fast)
1. Create a venv and install requirements.
2. Clone domains list [here](https://github.com/tb0hdan/domains), and merge it with `merge_datas.py`, or use other source  
3. Install [massdns](https://github.com/blechschmidt/massdns)
4. Run `massdns -r resolvers.txt -t A -o S -w results.txt domains.txt`
4. Use `massdns2list.py` to format the list
## Domains source
- Worldwide: <https://ipsniper.info/domaincount.html>, <https://github.com/tb0hdan/domains> (except .ru)
- .RU: <https://github.com/2naive/top_ru_domains_nameservers_list/blob/main/ru_alexa_top1m.txt>
- Top 17m list: <https://github.com/lkarlslund/topdomains>
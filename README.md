# rpz-detector
To make a public RPZ block list for everyone, open forever.  
## How it works?
### About RPZ
TWNIC's implementation of RPZ is an effective DNS-based defense mechanism that significantly enhances network security by blocking malicious domain names at the DNS level. It serves as a vital part of the network infrastructure, contributing to a safer and more reliable internet environment for users in Taiwan. By filtering out known threats before they can reach users, RPZ helps protect individuals and organizations from a wide range of cyber threats.
### RPZ controversy
TL;DR: Taiwan's website blocking system, especially "RPZ 1.5" is controversial. It allows quick blocking without court approval, lacks transparency, and has a history of errors (it used to block eu.org, Polymarket.com and Instagram.com), raising concerns about potential abuse and the restriction of digital rights. The new law further legitimizes this process, sparking fears of unchecked government power online.
#### More info about it:
- <https://blog.ocf.tw/2024/10/ocf_14.html> [Wayback machine](https://web.archive.org/web/2/https://blog.ocf.tw/2024/10/ocf_14.html)
- <https://www.facebook.com/seadog007/posts/pfbid02K7KwLyrchHEoWEVbG4bxQCxnLq81Dj6f4ig9Qt5nbGWsgj3zsfXqc9EATgvwo8CUl> [Wayback machine](https://web.archive.org/web/20230607001325/https://www.facebook.com/seadog007/posts/pfbid02K7KwLyrchHEoWEVbG4bxQCxnLq81Dj6f4ig9Qt5nbGWsgj3zsfXqc9EATgvwo8CUl)
### Okay, so how it works??
RPZ only effect Taiwanese DNS (Maybe), like Quad 101 (101.101.101.101) or HiNet DNS (168.95.1.1). And Quad 101 have a additional record if the domain is blocked by RPZ, so we check if there have the keyword like "rpz" or "rpztw" to check if the domains is blocked by RPZ.
## Download RPZ block list
Not yet, but you can make it yourself with steps below
## Setup
1. Create a venv and install requirements.
2. Clone domains list [here](https://github.com/tb0hdan/domains), and merge it with `merge_datas.py` 
3. Check if the domains is still alive with [massdns](https://github.com/blechschmidt/massdns) (optional)
4. Config to your want in main.py (optional)
5. Run main.py then waiting for a while (maybe a day or so)
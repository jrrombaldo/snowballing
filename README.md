# scraper
anonymous scraping multi-thread tool



there is a problem to install cryptography on apple m1, to overcome:
```
LDFLAGS="-L$(brew --prefix openssl@1.1)/lib" CFLAGS="-I$(brew --prefix openssl@1.1)/include" pip install cryptography
```
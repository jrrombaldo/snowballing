# Snowballing

This tool takes a bibliography file and determines both citations and references searching - in academic terms, forward and backwards snowballing, respectively. For each identified article, it lookup all details available, such as authors, journals, publications, and more.

It uses SemanticScholar.org as its search engine for snowballing and metadata lookup and retrieval. the only required input is bibliography file on [RIS format](https://en.wikipedia.org/wiki/RIS_(file_format)).

## Implementation details
It mixes the SemanticScholar API and WebPage searching because the API alone does not always find the papers the WebPage does. Hence, the approach to use the API first, and if nothing is returned, then use the WebPage. Studies not found on both API and WebPage are registered into TXT file (`./results/not-found.txt`)

Snowballing generally returns hundreds, if not thousands, of studies and to speed things up, this tool can use multiple threads and process searches in parallel; consequently, there is a high likelihood of hitting the SemanticScholar requests rate limit. To overcome throttling and rate-limit issues, it can use [TOR network](https://en.wikipedia.org/wiki/Tor_(network)), allocating a TOR circuit for each thread. This is, each thread will have a distinct internet IP and be seen as a different client. Use the parameter `--tor` to enable TOR networks.

This tool implements a thread pooling approach, where a thread is allocated (including its TOR circuit) for a single paper search, and when the search is done, it terminates the thread, launching a new one for the following paper. The parameter `--thread <number>` controls the maximum number of threads running at a given time.
## How to run it

### Preparing the environment
```
git clone git@github.com:jrrombaldo/snowballing.git
cd snowballing
python3 -m venv ./venv
source ./venv/bin/activate
python3 -m pip install --upgrade pip    
pip install -r ./requirements.txt
```

## Execution details
```
source ./venv/bin/activate
python ./snowballing --threads 75 --tor ./bibliography.ris
```


### Potential issues
Due to OpenSSL version compatibility problems, Apple M1 users may face issues installing its dependencies, namely cryptography. To overcome it, try the following:
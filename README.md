# Crawler examples using Selenium

### Prerequisites
* Install chromedriver: https://chromedriver.chromium.org/downloads
    - Uploaded `chromedriver` is for Chrome version 77 (ChromeDriver 77.0.3865.40)
* Install selenium
    ```
    pip install selenium
    ```

### Examples
1. Chromium bug report Crawler ([script](./chrome_bug_crawler.py))
    - Crawl all issues occured in `JavaScript` component
    - URL: https://bugs.chromium.org/p/chromium/issues/list?q=component%3ABlink%3EJavaScript%20&can=1
    - Crawled data: bug id, report date, owner, status, ...
2. Google Code Jam Cralwer ([script](./gcj_crawler.py))
    - Crawl all correct solutions saved in Google Code Jam archive
    - URL: https://codingcompetitions.withgoogle.com/codejam/archive
    - Crawled data: contestant name, country, solution, ...
    - Download solutions in `downloads` folder

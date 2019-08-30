from core_framework.crawlers import CrawlerBase


class MyCrawler(CrawlerBase):

    def master(self):
        # proc_id is important when we have multithread or multiprocessing in play
        proc_id = 1

        # prepare new request for this thread/process and return proxy sha
        sha = self.new_request(proc_id=proc_id)

        # tic_time is used for long loops where releasing same proxy will not happen longer than 30
        self.tic_time(sha, proc_id)

        # acquire request and set request type on 2 (number 2 is GET request with proxy)
        r = self.requests.get(proc_id)
        r.request_type = 2

        # then go to the web page and return response
        r.go('http://api.ipify.org/')
        html = r.response.content  # if you want beautiful soup object
        print(html)
        html = r.response.content_raw  # if you want raw bytes html

        # parse data do another request etc.

        # release proxy back in use if it is not released it will be not be available for that web_base next 30min
        self.release_proxy(sha)


if __name__ == '__main__':
    api = MyCrawler('ipify.org/')
    api.master()
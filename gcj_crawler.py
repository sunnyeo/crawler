#!/usr/bin/python3 -B

from crawler.crawler import Crawler

import os
import csv
import time
from selenium.webdriver.common.by import By

class GCJCrawler(Crawler):
    def __init__(self):
        super().__init__('./chromedriver', headless=False)

    def _get_prob_info(self):
        id_list = self.driver.execute_script(
            'var id_list = []; \
            for (i = 0; i < GCJ.problems.length; i++) { \
                id_list[i] = {}; \
                id_list[i]["id"] = GCJ.problems[i].id; \
                id_list[i]["io"] = GCJ.io[i].length; \
            }; \
            return id_list;'
        )
        return id_list

    def _parse_old_ver(self, url, round_cnt, prob_cnt):
        print (url)
        index = int(url.split('/')[-2])
        board_url = url.replace('dashboard', 'scoreboard?c=%d#vf=1' %index)

        author_info_list = []
        while True:
            print (board_url)
            self.driver.get(board_url)

            prob_info = self._get_prob_info()

            author_list = self.get_all_elements(By.CSS_SELECTOR, '#scb-table-body > tr')
            for author in author_list:
                author_info = {}
                info_list = self.get_all_elements(By.TAG_NAME, 'td', element=author)

                prob_index = 0
                prob_io_index = 0
                new_prob_cnt = prob_cnt
                for i, info in enumerate(info_list):
                    if i == 0:
                        author_info['rank_%d' %round_cnt] = info.text.replace('\n ', '')
                    elif i == 1:
                        country = self.get_element(By.TAG_NAME, 'img', element=info)
                        country = country.get_attribute('title')
                        author_info['country'] = country.replace(' ', '_')

                    elif i == 2:
                        author_info['name'] = info.text
                    elif i == 3:
                        author_info['score_%d' %round_cnt] = info.text
                    elif i == 4:
                        continue
                    else:
                        if '--' in info.text or 'Time' in info.text:
                            author_info['prob_%d' %new_prob_cnt] = None
                        else:
                            download_url = url.replace('dashboard', 
                            'scoreboard/do/?cmd=GetSourceCode&problem=')
                            download_url += '%s&io_set_id=%d&username=%s' %(
                                prob_info[prob_index]['id'],
                                prob_io_index,
                                author_info['name']
                            )
                            sol_path = self.code_path + '/%s_%s_%d.zip' \
                                                        %(author_info['name'],
                                                        author_info['country'],
                                                        new_prob_cnt)
                            # sol = self.get_all_elements(By.TAG_NAME, 'img', element=info)[1]
                            # sol.click()
                            # alert = self.driver.switch_to_alert()
                            # alert.accept()
                            
                            print ('Move to %s' %sol_path)
                            download = self.download_file_url(download_url, sol_path)
                            if download:
                                author_info['prob_%d' %new_prob_cnt] = sol_path
                            else:
                                author_info['prob_%d' %new_prob_cnt] = 'Fail'

                        if prob_info[prob_index]['io'] == (prob_io_index + 1):
                            prob_index += 1
                            prob_io_index = 0
                        else:
                            prob_io_index += 1
                        new_prob_cnt += 1

                print (author_info)
                author_info_list.append(author_info)

            next_page = self.get_all_elements(By.CSS_SELECTOR, '#scb-range-links > a')[-1]
            if 'Next' in next_page.text:
                next_page.click()
                board_url = self.driver.current_url
                self.driver.execute_script('window.open()')
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[-1])
            else:
                break
            
        return author_info_list, new_prob_cnt

    def _get_solution(self, author_info, url, total_prob, prob_cnt):
        print (url)
        self.driver.execute_script('window.open()')
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get(url)

        board = self.get_all_elements(By.CSS_SELECTOR, 
                                '#scoreboard > div > div:nth-child(2) > div')

        prob_info = {}
        for i in range(total_prob):
            prob_info['prob_%d' %i] = None

        while True:
            for i, row in enumerate(board):
                if i == 0:
                    continue
                elif row.text == '':
                    break
                else:
                    for p in range(total_prob):
                        if prob_info['prob_%d' %p] is None:
                            prob = self.get_element(By.CSS_SELECTOR, 
                            'div.ranking-table__row > div:nth-child(%d)' %(p+1), element=row)

                            if 'check' in prob.text:
                                try:
                                    sol = self.get_element(By.TAG_NAME, 'button', element=prob)
                                    sol.click()
                                    sol_path = self.code_path + '/%s_%s_%d.txt' \
                                                                    %(author_info['name'],
                                                                    author_info['country'],
                                                                    prob_cnt+p)
                                    self.download_file_click(sol_path)
                                    prob_info['prob_%d' %p] = sol_path
                                except:
                                    # No solution
                                    pass

            next_prob = self.get_element(By.CLASS_NAME, 'nav-chevron-right')
            if next_prob.get_attribute('disabled'):
                break
            else:
                next_prob.click()            
            

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        return prob_info

    def _parse_new_ver(self, url, round_cnt, prob_cnt):
        print (url)
        self.driver.get(url)

        before_rank = ''
        author_info_list = []
        while True:
            prob_list = self.get_all_elements(By.CLASS_NAME, 
                                    'problems-bar-graphs-aggregate-graphs')
            total_prob = len(prob_list)

            author_list = self.get_all_elements(By.CSS_SELECTOR, 
                                    '#scoreboard > div:nth-child(1) > div:nth-child(1) > div')

            for i, author in enumerate(author_list):
                if i == 0:
                    continue

                author_info = {}
                info_list = self.get_all_elements(By.TAG_NAME, 'div', element=author)
                for j, info in enumerate(info_list):
                    if j == 0:
                        if i == 1:
                            while(before_rank == info.text):
                                pass
                            before_rank = info.text
                        author_info['rank_%d' %round_cnt] = info.text
                    elif j == 1:
                        link = self.get_element(By.TAG_NAME, 'a', element=info)
                        info2 = self.get_element(By.TAG_NAME, 'p', element=link)
                        author_info['name'] = info2.text
                        country = self.get_element(By.TAG_NAME, 'img', element=info2)
                        country = country.get_attribute('src')
                        country = country.split('/')[-1].split('-')[0]
                        author_info['country'] = country

                        sol_link = link.get_attribute('href')
                        prob_info = self._get_solution(author_info, sol_link, 
                                                        total_prob, prob_cnt)
                        author_info.update(prob_info)
                    elif j == 2:
                        score = self.get_element(By.TAG_NAME, 'span', element=info)
                        author_info['score_%d' %round_cnt] = score.text

                print (author_info)
                author_info_list.append(author_info)

            pagination = self.get_element(By.CLASS_NAME, 'ranking-table-pagination')
            next_page = self.get_element(By.CSS_SELECTOR, 
            'div.ranking-table-pagination-pane.ranking-table-pagination-pane__right > \
            button:nth-child(4)', element=pagination)
            if next_page.get_attribute('disabled'):
                break
            else:
                next_page.click()
            
        return author_info_list, prob_cnt+total_prob

    def run(self):
        for year in range(2008, 2020):
            year_url = 'https://codingcompetitions.withgoogle.com/' + \
                        'codejam/archive/%d' %year
            self.driver.get(year_url)
            print (year_url)

            self.code_path = '/data/crawler/downloads/GCJ/%d' %year
            if not os.path.exists(self.code_path):
                os.makedirs(self.code_path)
        
            self.get_all_elements(By.CLASS_NAME, 'schedule-row')
            round_count = len(self.get_all_elements(By.CLASS_NAME, 'schedule-row'))

            total_author_info = {}
            prob_cnt = 0
            for cnt in range(1, round_count+1):
                self.driver.get(year_url)
                round_url = self.get_element(By.ID, 'archive-view-cta-%d' %cnt)
                round_url = round_url.get_attribute('href')

                if '/dashboard' in round_url:
                    author_info_list, prob_cnt = \
                                    self._parse_old_ver(round_url, cnt, prob_cnt)
                else:
                    author_info_list, prob_cnt = \
                                    self._parse_new_ver(round_url, cnt, prob_cnt)
                
                for author_info in author_info_list:
                    key = '%s.%s' %(author_info['name'], author_info['country'])
                    if key in author_info:
                        total_author_info[key].update(author_info)
                    else:
                        total_author_info[key] = author_info

            with open('gcj_result_%d.csv' %year, 'w') as csvfile:
                fieldnames = total_author_info.keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for author_info in total_author_info:
                    writer.writerow(author_info)

c = GCJCrawler()
c.run()

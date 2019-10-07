#!/usr/bin/python3 -B

from crawler.crawler import Crawler

import csv
import copy
import datetime
from dateutil.parser import parse
from selenium.webdriver.common.by import By

open_status = ['Unconfirmed', 'Untriaged', 'Available', 'Assigned', 'Started']
close_status = ['Fixed', 'Verified', 'Duplicate', 'WontFix', 'ExternalDependency', 
                'FixUnreleased', 'Invalid']

class V8Crawler(Crawler):
    def __init__(self):
        super().__init__('./chromedriver')

    def _parse_timestamp(self, element):
        date = element.get_attribute('title').split(' ')
        date = parse(' '.join(date[:6]))
        return date.strftime('%Y-%m-%d')

    def _calculate_days(self, date1, date2):
        td = date2 - date1
        return td.days

    def _get_report_date(self, shadow_root2):
        report_date = ''
        
        shadow_root3 = self.get_shadow_root(By.TAG_NAME, 'mr-issue-header', 
                                            element=shadow_root2)

        report_date = self.get_element(By.TAG_NAME, 'chops-timestamp', 
                                        element=shadow_root3)
        return self._parse_timestamp(report_date)

    def _get_labels_in_comments(self, shadow_root3):
        labels = {}

        shadow_root4 = self.get_shadow_root(By.TAG_NAME, 'mr-comment-list', 
                                            element=shadow_root3)

        try:
            comment_list = self.get_all_elements(By.TAG_NAME, 'mr-comment', 
                                                element=shadow_root4)
        except:
            print ('No comment')
            return labels

        for comment in comment_list:
            shadow_root5 = self.expand_shadow_element(comment)

            div_list = self.get_all_elements(By.TAG_NAME, 'div', 
                                            element=shadow_root5)

            label_value = {}
            for div in div_list:
                if div.get_attribute('class') == 'comment-header':
                    if 'Deleted' in div.text:
                        continue
                    comment_date = self.get_element(By.TAG_NAME, 'chops-timestamp',
                                                    element=div)
                    comment_date = self._parse_timestamp(comment_date)
                    label_value['date'] = comment_date

                elif div.get_attribute('class') == 'issue-diff':
                    for attr in div.text.split('\n'):
                        text = attr.replace(' ', '')
                        key = text.split(':')[0]
                        value = ':'.join(text.split(':')[1:])
                        if key == '' or value == '':
                            continue
                        label_value['value'] = value
                        if key in labels:
                            labels[key].append(copy.deepcopy(label_value))
                        else:
                            labels[key] = [copy.deepcopy(label_value)]
        return labels

    def _get_first_last_status(self, status_list):
        start = None
        end = None
        for status_info in status_list:
            status = status_info['value'].split('(')[0]
            date = parse(status_info['date'])

            if status in open_status:
                if start is None:
                    start = {'status': status, 'date': date}
                else:
                    if date < start['date']:
                        start = {'status': status, 'date': date}
            elif status in close_status:
                if end is None:
                    end = {'status': status, 'date': date}
                else:
                    if date > end['date']:
                        end = {'status': status, 'date': date}
        return (start, end)

    def _get_bug_info(self, bug_id):
        url = 'https://bugs.chromium.org/p/chromium/issues/detail?id=%s' \
            %bug_id

        info = {}
        try_cnt = 1
        while True:
            try:
                self.driver.get(url)
                shadow_root1 = self.get_shadow_root(By.TAG_NAME, 'mr-app')
                shadow_root2 = self.get_shadow_root(By.TAG_NAME, 'mr-issue-page', 
                                                    element=shadow_root1)
                shadow_root3 = self.get_shadow_root(By.TAG_NAME, 'mr-issue-details', 
                                                    element=shadow_root2)
                break
            except:
                print ('[ERROR]: %d' %try_cnt)
                try_cnt += 1
                continue

        report_date = self._get_report_date(shadow_root2)
        labels = self._get_labels_in_comments(shadow_root3)
    
        info['bug_id'] = bug_id
        info['report_date'] = report_date
        for key, value in labels.items():
            info[key] = value

        if 'Status' in labels:
            start, end = self._get_first_last_status(labels['Status'])

            if start is not None:
                # report ~ assign
                info['days1'] = self._calculate_days(parse(report_date), start['date'])
            if start is not None and end is not None:
                # assign ~ finish
                info['days2'] = self._calculate_days(start['date'], end['date'])
            if end is not None:
                # report ~ finish
                info['total_days'] = self._calculate_days(parse(report_date), end['date'])

        return info

    def _get_bug_list(self, start):
        url = 'https://bugs.chromium.org/p/chromium/issues/list?' + \
            'colspec=ID%20Pri%20M%20Status%20Owner%20Summary&' + \
            'q=component%3ABlink>JavaScript%20&can=1&num=100&' + \
            'start=%d' %start
        self.driver.get(url)

        bug_id_list = []
        has_next = False

        bug_list = self.get_all_elements(By.CSS_SELECTOR, 'td.id.col_0')
        for bug_id in bug_list:
            bug_id_list.append(bug_id.text)

        pagination_list = self.get_all_elements(By.CLASS_NAME, 'pagination')
        for pagination in pagination_list:
            if 'Next' in pagination.text:
                has_next = True

        return has_next, bug_id_list

    def run(self):
        fieldnames = ['bug_id', 'report_date', 'Owner', 'Cc', 'Status', 
                    'days1', 'total_days', 'days2', 'Labels' , 'etc']
        with open('result.csv', 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            start = 0
            while True:
                has_next, bug_list = self._get_bug_list(start)
                for bug_id in bug_list:
                    print ('Start: %s' %bug_id)

                    bug_info = self._get_bug_info(bug_id)

                    filtered_bug_info = {}
                    for k, v in bug_info.items():
                        if k in fieldnames:
                            filtered_bug_info[k] = v
                        else:
                            if 'etc' in filtered_bug_info:
                                filtered_bug_info['etc'] += [v]
                            else:
                                filtered_bug_info['etc'] = [v]
                    writer.writerow(filtered_bug_info)

                if has_next is False:
                    break
                else:
                    start += 100
      

c = V8Crawler()
c.run()

# print (c._get_bug_list(0))
# print (c._get_bug_info('976627'))
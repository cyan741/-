'''
This script is used to define class crawler, which is used to crawl web info.
'''
import requests
from bs4 import BeautifulSoup
import time
import json
from tqdm import tqdm
from typing import Dict, List
import pandas as pd
import re
import pdb

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.46"
COOKIE = r"s_fid=64116D8E61735942-31EC6D99BABB0880;"
SLEEP_TIME = 0.2 # seconds

class Crawler:
    def __init__(self):
        pass

    def fetch_html(self, url):
        '''
        get html context
        '''
        # no vpn
        time.sleep(SLEEP_TIME)
        headers = {"User-Agent":USER_AGENT, "Cookie":COOKIE}
        response = requests.get(url=url, headers=headers)
        response.encoding = response.apparent_encoding
        return response.text
    
    def get_base_url(self, url:str)->str:
        pattern = r'http.{,}cn'
        result = re.match(pattern, url)
        base_url = result.group()
        return base_url
    
    def fetch_files(self, url:str, file_lists_locator:Dict, single_file_locator:List)->List:
        '''
        get all file list from a url
        ''' 
        base_url = self.get_base_url(url)
        file_list = []
        html = self.fetch_html(url)
        if not html:
            return None
        soup = BeautifulSoup(html, 'html.parser')
        method = file_lists_locator['method']
        tag = file_lists_locator['tag']
        class_ = file_lists_locator['class_']
        if method == 'find_all':
            soup_results = soup.find_all(tag, class_=class_)
        # pdb.set_trace()
        for i, bs_item in enumerate(soup_results):
            file_item = self.get_file_info(bs_item, single_file_locator)
            if not file_item:
                continue
            file_item["link"] = base_url + file_item["link"]
            file_list.append(file_item)
        return file_list
    
    def get_file_info(self, bs_item, single_file_locator:List)->Dict:
        file_info = {}
        for item in single_file_locator:
            info = item["info"]
            tag = item['tag']
            class_ = item['class_']
            if not class_:
                try:
                    file_info[info] = bs_item.find(tag).text.strip()
                except:
                    return None
            elif class_ != 'title' and info == 'title':
                try:
                    file_info[info] = bs_item.find(tag, class_=class_).text.strip()
                except:
                    return None
                # pdb.set_trace()
            else:
                try:
                    file_info[info] = bs_item.find(tag).get(class_)
                except:
                    return None
        return file_info
    
    def get_webs_file(self)->List:
        '''
        from web_list.json get all files' info and save in dataframe
        '''
        all_file_items = []
        with open("./web_list.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for web in tqdm(data):
            web_url = web["url"]
            
            file_lists_locator = web["file_lists_locator"]
            single_file_locator = web["single_file_locator"]
            for i in range(50):

                url = web_url.replace('{page_num}', str(i+1))
                file_list = self.fetch_files(url, file_lists_locator, single_file_locator)
                if not file_list:
                    break
                all_file_items.extend(file_list)
        return all_file_items
    
    def save_results(self)->pd.DataFrame:
        file_list = self.get_webs_file()
        df = pd.DataFrame(file_list)
        df.to_csv('file_list.csv', index=False)
        return df


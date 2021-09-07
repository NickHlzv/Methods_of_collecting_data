import scrapy
import re
import json
from scrapy.http import HtmlResponse
from urllib.parse import urlencode
from copy import deepcopy
from lesson8.instaparser.items import InstaparserItem



class InstaparserSpider(scrapy.Spider):
    name = 'instaparser'
    allowed_domains = ['instagram.com']
    start_urls = ['https://instagram.com/']
    insta_login = 'Onliskill_udm'
    insta_pass = '#PWD_INSTAGRAM_BROWSER:10:1629825416:ASpQAMvl1EAdo0NdRZNcM1/pjlU9rRg4n4cjCM00SDGSV5pDN6XbC93ZbYN67HUOHkXZnGGe2gIWPU2qtQY0HAkIjR5U5syu+lv8qtqeI7cyy2ua6WmBV6AngVo1apn3eJ6O3UAFVgb+q5HtHsQ='
    insta_login_link = 'https://www.instagram.com/accounts/login/ajax/'
    users_parse = ['allegaeonofficial', 'digimortal_band']

    def parse(self, response: HtmlResponse):
        csrf = self.fetch_csrf_token(response.text)
        yield scrapy.FormRequest(self.insta_login_link,
                                 method='POST',
                                 callback=self.user_login,
                                 formdata={'username': self.insta_login,
                                           'enc_password': self.insta_pass},
                                 headers={'X-CSRFToken': csrf})

    def user_login(self, response: HtmlResponse):
        j_body = response.json()
        if j_body['authenticated']:
            for user in self.users_parse:
                yield response.follow(f'/{user}',
                                      callback=self.set_api,
                                      cb_kwargs={'username': user})

    def set_api(self, response: HtmlResponse, username):
        user_id = self.fetch_user_id(response.text, username)
        # Запрос подписчиков
        variables = {
            'count': 12,
            'search_surface': 'follow_list_page'
        }
        api_url = f'https://i.instagram.com/api/v1/friendships/{user_id}/followers/?{urlencode(variables)}'

        yield response.follow(api_url,
                              callback=self.parse_api,
                              cb_kwargs={'user_id': user_id,
                                         'username': username,
                                         'variables': deepcopy(variables),
                                         'target': 'followers'})

        # Не отходя от кассы сразу запрос подписок
        variables_following = {
            'count': 12,
        }

        api_url_following = f'https://i.instagram.com/api/v1/friendships/{user_id}/following/?{urlencode(variables_following)} '
        yield response.follow(api_url_following,
                              callback=self.parse_api,
                              cb_kwargs={'user_id': user_id,
                                         'username': username,
                                         'variables': deepcopy(variables_following),
                                         'target': 'following'})

    def parse_api(self, response: HtmlResponse, username, user_id, variables, target):
        if response.status == 200:
            j_data = response.json()
            if j_data.get('users'):
                variables['max_id'] = j_data.get('next_max_id')
                api_url = f'https://i.instagram.com/api/v1/friendships/{user_id}/{target}/?{urlencode(variables)}'
                yield response.follow(api_url,
                                      callback=self.parse_api,
                                      cb_kwargs={'username': username,
                                                 'user_id': user_id,
                                                 'variables': deepcopy(variables),
                                                 'target': target})

            users = j_data.get('users')
            for user in users:
                item = InstaparserItem(user_id=user.get('pk'),
                                       user_nick=user.get('username'),
                                       full_name=user.get('full_name'),
                                       picture=user.get('profile_pic_url'),
                                       category=target,
                                       parent_name=username,
                                       full_data=user)
                yield item

    # Получаем токен для авторизации
    def fetch_csrf_token(self, text):
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')

    # Получаем id желаемого пользователя
    def fetch_user_id(self, text, username):
        matched = re.search(
            '{\"id\":\"\\d+\",\"username\":\"%s\"}' % username, text
        ).group()
        return json.loads(matched).get('id')

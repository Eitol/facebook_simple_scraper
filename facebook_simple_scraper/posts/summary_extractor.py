import abc
import re
from datetime import datetime
from typing import List, Tuple

import dateparser
from bs4 import BeautifulSoup, Tag
from dateutil.parser import parse

from facebook_simple_scraper.entities import Post, PostList


class PostSummaryHTMLParser(abc.ABC):
    @abc.abstractmethod
    def extract_posts(self, html_content: str) -> PostList:
        raise NotImplementedError()


class PostSummaryListExtractor(PostSummaryHTMLParser):
    def extract_posts(self, html_content: str) -> PostList:
        return self._extract_posts_from_html(html_content)

    def _extract_posts_from_html(self, html_content: str) -> PostList:
        results: List[Post] = []
        soup = BeautifulSoup(html_content, 'html.parser')
        feeds = self._extract_post_tags(soup)
        for feed in feeds:
            post_summary = self._extract_post_from_tag(feed)
            results.append(post_summary)
        cursor, profile_id = self._extract_next_page_params(soup)
        # sort by date
        results.sort(key=lambda x: x.date, reverse=True)
        return PostList(
            posts=results, cursor=cursor, profile_id=profile_id,
        )

    def _extract_post_from_tag(self, feed: BeautifulSoup) -> Post:
        text, text_tag = self._extract_post_text(feed)
        like_count = self._extract_like_count(feed)
        image_tag = feed.find('a', class_='cf cg ch')
        image_url = ''
        if image_tag is None:
            image_tag = feed.find('img', src=re.compile(r'https://.*\.fna\.fbcdn\.net/v/'))
            if image_tag is not None:
                image_url = image_tag.attrs['src']
        else:
            image_url = image_tag.attrs['href']
        story_id = self._extract_story_id(feed)
        comment_count = self._extract_comments_count(feed)
        # in format like "'May 2 at 1:27 PM'"
        post_date = self._extract_post_date(feed)
        return Post(
            id=story_id,
            url=f'https://www.facebook.com/{story_id}',
            text=text,
            image_url=image_url,
            video_url='',
            like_count=like_count,
            comment_count=comment_count,
            date=post_date
        )

    @staticmethod
    def _extract_post_tags(soup: BeautifulSoup) -> List[BeautifulSoup]:
        feeds = soup.find_all('article')
        if feeds is None or len(feeds) == 0:
            feeds = soup.find_all('div', class_='_55wo _56bf _5rgl')
            if feeds is None or len(feeds) == 0:
                feeds = soup.find_all('div', class_='bm bn bo')
        if feeds is None or len(feeds) == 0:
            return []
        return feeds

    @staticmethod
    def _extract_post_text(feed: BeautifulSoup) -> Tuple[str, Tag]:
        text_tag = feed.find('div', class_='_5rgn')
        text = ''
        if text_tag is not None:
            text = text_tag.get_text(strip=True)
        if text == '':
            text_tag = feed.find_all('div', class_='ca')
            if text_tag is not None and len(text_tag) > 0:
                text = text_tag[0].get_text(strip=True)
        if text == '':
            text_tag = feed.find('td', class_='t bs')
            if text_tag is not None:
                text = text_tag.get_text(strip=True)
        return text, text_tag

    @staticmethod
    def _extract_like_count(feed: Tag) -> int:
        likes_tag = feed.find('a', class_='_2e4w nowrap')
        if likes_tag is None:
            likes_tag = feed.find('a', class_='cn co')
            if likes_tag is None:
                return 0
        try:
            return int(likes_tag.get_text(strip=True).replace(",", '').split(' ')[-1])
        except:
            return 0

    @classmethod
    def _extract_post_date(cls, feed: BeautifulSoup) -> datetime:
        post_date_str = feed.find("abbr").text
        post_date = cls._parse_date(post_date_str)
        return post_date

    @staticmethod
    def _extract_comments_count(feed: BeautifulSoup) -> int:
        comments_text = feed.find(string=re.compile(r'\d+ Comments'))
        if comments_text is not None:
            return int(re.search(r'\d+', comments_text).group())
        return 0

    @staticmethod
    def _parse_date(date_string: str) -> datetime:
        """
        Parse date string to datetime object.
        Example date_string: 'May 2 at 1:27 PM'
        :param date_string:
        :return:
        """
        try:
            return dateparser.parse(date_string)
        except Exception as e:
            return parse(date_string.replace('at', ''))

    @staticmethod
    def _extract_next_page_params(soup: BeautifulSoup) -> Tuple[str, str]:
        cursor_tags = soup.find_all('a')
        cursor = ''
        profile_id = ''
        for cursor_tag in cursor_tags:
            if 'cursor=' in cursor_tag['href']:
                cursor = cursor_tag['href'].split('cursor=')[1]
                cursor = cursor.split('&')[0]
                profile_id = cursor_tag['href'].split('profile_id=')[1]
                profile_id = profile_id.split('&')[0]
                break
        return cursor.strip().replace("'", ''), profile_id.strip()

    @staticmethod
    def _extract_story_id(feed: BeautifulSoup) -> str:
        story_id = ''
        story_id_regex = re.compile(r'/story.php\?story_fbid=\d+')
        story_id_query_params_tag = feed.find('a', href=story_id_regex)
        if story_id_query_params_tag is not None and 'href' in story_id_query_params_tag.attrs:
            story_id_query_params = story_id_query_params_tag['href'].split('story_fbid=')[1]
            story_id = story_id_query_params.split('&')[0]
        else:
            story_id_regex = re.compile(r'/photo.php\?fbid=\d+')
            story_id_query_params_tag = feed.find('a', href=story_id_regex)
            if story_id_query_params_tag is not None and 'href' in story_id_query_params_tag.attrs:
                story_id_query_params = story_id_query_params_tag['href'].split('fbid=')[1]
                story_id = story_id_query_params.split('&')[0]
        if story_id in [None, '']:
            story_id_regex = re.compile(r'/reactions/picker/\?ft_id=\d+')
            story_id_query_params_tag = feed.find('a', href=story_id_regex)
            if story_id_query_params_tag is not None and 'href' in story_id_query_params_tag.attrs:
                story_id = story_id_query_params_tag['href'].split('ft_id=')[1]
        if story_id in [None, '']:
            story_id = PostSummaryListExtractor._extract_story_id_by_like_tag(str(feed))
        return story_id

    @staticmethod
    def _extract_story_id_by_like_tag(html_content: str) -> str:
        soup = BeautifulSoup(html_content, 'html.parser')
        span = soup.find('span', id=lambda x: x and x.startswith('like_'))
        if span is None:
            return ''
        if 'id' not in span.attrs:
            return ''
        s = span['id'].split('_')
        if len(s) < 2:
            return ''
        return s[1]

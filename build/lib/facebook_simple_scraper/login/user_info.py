from bs4 import BeautifulSoup

from facebook_simple_scraper.entities import UserInfo
from facebook_simple_scraper.error_dict import LoginFailedException


class UserInfoExtractor:
    @classmethod
    def extract_user_info(cls, html_resp: str) -> UserInfo:
        soup = BeautifulSoup(html_resp, 'html.parser')
        # <div class="n o p" style="" id="login_error">
        login_error = soup.find('div', id='login_error')
        if login_error or soup is None:
            raise LoginFailedException("Login failed")
        target = soup.find('input', {'type': 'hidden', 'name': 'target'}).attrs['value']
        fb_dtsg = soup.find('input', {'type': 'hidden', 'name': 'fb_dtsg'}).attrs['value']
        username = ""
        profile_name = ""
        user_link = soup.find('a', href=True, class_='gr gs')
        if user_link:
            user_url = user_link['href']
            # Extraer el nombre de usuario desde la URL
            user_name_start = user_url.find('/') + 1
            user_name_end = user_url.find('?', user_name_start)
            username = user_url[user_name_start:user_name_end]
            profile_name = user_link.text
            if '.php' in username:
                username = ''
            if profile_name != '' and username != '':
                return UserInfo(
                    username=username,
                    profile_name=profile_name,
                    target=target if target else '',
                    fb_dtsg=fb_dtsg if fb_dtsg else '',
                )
        if username == '':
            user_links_classes = ['fp', 'bg be bf', 'gq', 'by bz r']
            profile_name = ""
            for user_link_class in user_links_classes:
                user_link = soup.find('a', href=True, class_=user_link_class)
                if user_link:
                    user_url = user_link['href']
                    # Extraer el nombre de usuario desde la URL
                    user_name_start = user_url.find('/') + 1
                    user_name_end = user_url.find('?', user_name_start)
                    username = user_url[user_name_start:user_name_end]
                    if '.php' in username or '=' in username:
                        username = ''
                        continue
                    else:
                        break

        if profile_name == '':
            profile_name_classes = ["by bz r", 'fq fr', 'bz r']
            for profile_name_class in profile_name_classes:
                profile_name_tag = soup.find('img', class_=profile_name_class)
                if profile_name_tag:
                    t = profile_name_tag.text.split(',')[0]
                    if len(t) > 0:
                        profile_name = t
                        break
                    alt = profile_name_tag.get('alt')
                    if alt:
                        profile_name = alt.split(',')[0]
                        break
        if '=' in username:
            username = ''
        return UserInfo(
            username=username,
            profile_name=profile_name,
            target=target,
            fb_dtsg=fb_dtsg,
        )

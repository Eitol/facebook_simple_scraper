import datetime
import json
from typing import List, Optional, Tuple

from facebook_simple_scraper.entities import Comment, Reaction, ReactionType, User


class GQLPostDetailExtractor:

    def extract(self, content: str) -> Tuple[List[Comment], List[Reaction], str]:
        j = self._read_first_json(content)
        if j is None:
            return [], [], ""

        top_reactions: List[Reaction] = []

        feedback_field = {}
        with_feedback = False
        try:
            feedback_field = j['data']['feedback']['ufi_renderer']['feedback']
            with_feedback = True
        except:
            pass
        if len(feedback_field) > 0:
            try:
                raw_top_reactions = feedback_field['comet_ufi_summary_and_actions_renderer'] \
                    ['feedback']['top_reactions']['edges']
                for r in raw_top_reactions:
                    reaction = Reaction(
                        type=self._classify_reaction_type(r['node']['id']),
                        count=r['reaction_count']
                    )
                    top_reactions.append(reaction)
                with_feedback = True
            except:
                pass

        extracted_comment: List[Comment] = []
        cursor = ''

        try:
            # "/comment_list_renderer/feedback/comment_rendering_instance_for_feed_location/comments/edges/3/node/body"
            raw_comments = j['data']['node']['comment_rendering_instance_for_feed_location']['comments']
            for node in raw_comments['edges']:
                extracted_comment.append(self._parse_raw_comment(node))
            cursor = raw_comments['page_info']['end_cursor']
        except:
            pass

        if with_feedback and len(extracted_comment) == 0:
            raw_comments = feedback_field['comment_list_renderer']['feedback']['comment_rendering_instance_for_feed_location']['comments']
            for node in raw_comments['edges']:
                extracted_comment.append(self._parse_raw_comment(node))
            cursor = raw_comments['page_info']['end_cursor']

        return extracted_comment, top_reactions, cursor

    def _parse_raw_comment(self, node):
        author = node['node']['author']
        reply_count = node['node']['feedback']['replies_fields']['total_count']
        user = self._extract_comment_user(author)
        comment_id = node['node']['legacy_fbid']
        if node['node']['body'] is not None:
            comment_text = node['node']['body']['text']
        else:
            comment_text = ""
        comment_url, created_at, reactions = self._extract_reactions(node)
        comment = Comment(
            id=comment_id,
            text=comment_text,
            date=created_at,
            user=user,
            url=comment_url,
            reactions=reactions,
            replies=[],
            replies_count=reply_count,
        )
        return comment

    @classmethod
    def _extract_reactions(cls, node: dict) -> tuple:
        reactions: List[Reaction] = []
        created_at = None
        comment_url = ""
        for al in node["node"]["comment_action_links"]:
            if al['__typename'] == 'XFBCommentTimeStampActionLink':
                c = al['comment']
                comment_url = c['url']
                created_at_epoch = c['created_time']
                created_at = datetime.datetime.fromtimestamp(created_at_epoch)
            elif al['__typename'] == 'XFBCommentReactionActionLink':
                for r in al['comment']['feedback']['top_reactions']['edges']:
                    count = r['reaction_count']
                    r_type_id = r['node']['id']
                    r_type = cls._classify_reaction_type(r_type_id)
                    reactions.append(Reaction(type=r_type, count=count))
        return comment_url, created_at, reactions

    @staticmethod
    def _extract_comment_user(author):
        user = User(
            id=author['id'],
            name=author['name'],
            gender=author['gender'],
            photo=author['profile_picture_depth_0']['uri']
        )
        return user

    @staticmethod
    def _classify_reaction_type(r_type_id: str) -> ReactionType:
        if r_type_id == "1635855486666999":
            return ReactionType.LIKE
        elif r_type_id == "1678524932434102":
            return ReactionType.LOVE
        elif r_type_id == "613557422527858":
            return ReactionType.CARE
        elif r_type_id == "478547315650144":
            return ReactionType.WOW
        elif r_type_id == "115940658764963":
            return ReactionType.HAHA
        elif r_type_id == "908563459236466":
            return ReactionType.SAD
        elif r_type_id == "444813342392137":
            return ReactionType.ANGRY
        return ReactionType.UNKNOWN

    @staticmethod
    def _read_first_json(content) -> Optional[dict]:
        key_counter = 0
        start_json = None
        end_json = None
        for i, c in enumerate(content):
            if c == '{':
                if key_counter == 0:
                    start_json = i
                key_counter += 1
            elif c == '}':
                key_counter -= 1
                if key_counter == 0:
                    end_json = i + 1
                    break

        if start_json is not None and end_json is not None:
            first_json_str = content[start_json:end_json]
            try:
                primer_json = json.loads(first_json_str, strict=False)

                return primer_json
            except json.JSONDecodeError as e:
                return None
        else:
            return None


if __name__ == '__main__':
    parser = GQLPostDetailExtractor()
    file_path = '//facebook_simple_scraper/tests/files/get_comments_gql_page_1.jsonlines'
    with open(file_path, 'r') as file:
        text = file.read()
        comments, reactions, next_cursor = parser.extract(text.__str__())
        print(comments)

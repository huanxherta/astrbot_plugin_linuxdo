from curl_cffi.requests import AsyncSession
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Node, Plain
import time

@register("linuxdo", "GeminiCLI", "LINUX DO 社区助手插件", "1.4.0")
class LinuxDoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.base_url = "https://linux.do"
        self.config = self.context.get_config()

    @filter.command("ld_top")
    async def get_top_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 全部热门话题'''
        yield event.plain_result("🔍 正在拉取 LINUX DO 热门话题...")
        
        limit = self.config.get("top_limit", 15)
        url = f"{self.base_url}/top.json?period=daily"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=20)
                resp.raise_for_status()
                data = resp.json()
                topics = self._filter_topics(data.get('topic_list', {}).get('topics', []), limit)
                
                if not topics:
                    yield event.plain_result("暂时没有找到热门话题。")
                    return
                
                yield event.chain_result(self._create_single_forward_node(event, topics, "🔥 热门话题"))
        except Exception as e:
            yield event.plain_result(f"❌ 获取失败: {str(e)}")

    @filter.command("ld_new")
    async def get_latest_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 最新讨论'''
        yield event.plain_result("✨ 正在拉取 LINUX DO 最新讨论...")
        
        limit = self.config.get("new_limit", 20)
        url = f"{self.base_url}/latest.json"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                topics = self._filter_topics(data.get('topic_list', {}).get('topics', []), limit)
                
                if not topics:
                    yield event.plain_result("暂时没有找到最新帖子。")
                    return
                
                yield event.chain_result(self._create_single_forward_node(event, topics, "✨ 最新讨论"))
        except Exception as e:
            yield event.plain_result(f"❌ 获取失败: {str(e)}")

    def _filter_topics(self, topics, limit):
        filter_pinned = self.config.get("filter_pinned", True)
        filtered = []
        for t in topics:
            if filter_pinned and (t.get('pinned') or t.get('pinned_globally')):
                continue
            filtered.append(t)
        return filtered[:limit]

    def _create_single_forward_node(self, event, items, title_prefix):
        bot_id = getattr(event, 'bot_id', '0')
        try: uin = int(bot_id)
        except: uin = 0
        show_author = self.config.get("show_author", True)
        full_text = f"{title_prefix} (共 {len(items)} 条)\n" + "━" * 15 + "\n\n"
        for i, t in enumerate(items):
            author_info = f" - @{t.get('last_poster_username')}" if show_author and t.get('last_poster_username') else ""
            full_text += f"{i+1}. {t.get('title')}{author_info}\n🔗 {self.base_url}/t/{t.get('id')}\n\n"
        return [Node(uin=uin, name="LINUX DO 助手", content=[Plain(full_text.strip())])]

from curl_cffi.requests import AsyncSession
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Node, Plain
import asyncio

@register("linuxdo", "GeminiCLI", "LINUX DO 社区助手插件", "1.6.0")
class LinuxDoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.base_url = "https://linux.do"
        self.config = self.context.get_config()

    @filter.command("ld_top")
    async def get_top_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 热门话题'''
        yield event.plain_result("🔍 正在拉取 LINUX DO 热门话题...")
        limit = self.config.get("top_limit", 15)
        topics = await self._fetch_all_pages(f"{self.base_url}/top.json?period=daily", limit)
        if not topics:
            yield event.plain_result("暂时没有找到热门话题。")
            return
        yield event.chain_result(self._create_single_forward_node(event, topics, "🔥 热门话题"))

    @filter.command("ld_new")
    async def get_latest_activity(self, event: AstrMessageEvent):
        '''获取 LINUX DO 最近活跃话题 (含新评论)'''
        yield event.plain_result("✨ 正在拉取 LINUX DO 最近活跃讨论...")
        limit = self.config.get("new_limit", 30)
        topics = await self._fetch_all_pages(f"{self.base_url}/latest.json", limit)
        if not topics:
            yield event.plain_result("暂时没有找到讨论。")
            return
        yield event.chain_result(self._create_single_forward_node(event, topics, "✨ 最近活跃"))

    @filter.command("ld_fresh")
    async def get_fresh_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 最新创建的话题 (不含旧帖评论)'''
        yield event.plain_result("🆕 正在拉取 LINUX DO 刚刚发布的新帖...")
        limit = self.config.get("fresh_limit", 20)
        # 使用 order=created 确保是按发布时间排序
        topics = await self._fetch_all_pages(f"{self.base_url}/latest.json?order=created", limit)
        if not topics:
            yield event.plain_result("暂时没有找到新发布的帖子。")
            return
        yield event.chain_result(self._create_single_forward_node(event, topics, "🆕 最新发布"))

    async def _fetch_all_pages(self, base_api_url, limit):
        all_topics = []
        page = 0
        sep = "&" if "?" in base_api_url else "?"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                while len(all_topics) < limit:
                    url = f"{base_api_url}{sep}page={page}"
                    resp = await s.get(url, timeout=15)
                    if resp.status_code != 200: break
                    data = resp.json()
                    topics = data.get('topic_list', {}).get('topics', [])
                    if not topics: break
                    filtered = self._filter_topics(topics)
                    all_topics.extend(filtered)
                    if len(all_topics) >= limit or len(topics) < 20: break
                    page += 1
                    await asyncio.sleep(0.5)
            return all_topics[:limit]
        except Exception:
            return all_topics[:limit] if all_topics else []

    def _filter_topics(self, topics):
        filter_pinned = self.config.get("filter_pinned", True)
        filtered = []
        for t in topics:
            if filter_pinned and (t.get('pinned') or t.get('pinned_globally')):
                continue
            filtered.append(t)
        return filtered

    def _create_single_forward_node(self, event, items, title_prefix):
        bot_id = getattr(event, 'bot_id', '0')
        try: uin = int(bot_id)
        except: uin = 0
        show_author = self.config.get("show_author", True)
        full_text = f"{title_prefix} (共 {len(items)} 条)\n" + "━" * 15 + "\n\n"
        for i, t in enumerate(items):
            author_info = f" (作者: {t.get('last_poster_username')})" if show_author and t.get('last_poster_username') else ""
            full_text += f"{i+1}. {t.get('title')}{author_info}\n🔗 {self.base_url}/t/{t.get('id')}\n\n"
        return [Node(uin=uin, name="LINUX DO 助手", content=[Plain(full_text.strip())])]

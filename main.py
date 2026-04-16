from curl_cffi.requests import AsyncSession
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Node, Plain, Forward
import asyncio
import time

@register("linuxdo", "GeminiCLI", "LINUX DO 社区助手", "1.7.1")
class LinuxDoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.base_url = "https://linux.do"
        self.config = self.context.get_config()

    @filter.command("ld_top")
    async def get_top_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 热门话题 (单气泡多节点)'''
        yield event.plain_result("🔍 正在拉取热门话题...")
        limit = self.config.get("top_limit", 30)
        topics = await self._fetch_all_pages(f"{self.base_url}/top.json?period=daily", limit)
        if not topics:
            yield event.plain_result("暂无数据。")
            return
        # 封装并发送
        nodes = self._create_forward_nodes(event, topics, "🔥 热门话题")
        yield event.chain_result([Forward(id=int(time.time()), nodes=nodes)])

    @filter.command("ld_new")
    async def get_latest_activity(self, event: AstrMessageEvent):
        '''获取 LINUX DO 最近活跃话题 (单气泡多节点)'''
        yield event.plain_result("✨ 正在拉取活跃讨论...")
        limit = self.config.get("new_limit", 60)
        topics = await self._fetch_all_pages(f"{self.base_url}/latest.json", limit)
        if not topics:
            yield event.plain_result("暂无数据。")
            return
        nodes = self._create_forward_nodes(event, topics, "✨ 最近活跃")
        yield event.chain_result([Forward(id=int(time.time()), nodes=nodes)])

    @filter.command("ld_time")
    async def get_time_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 最新发布的话题 (单气泡多节点)'''
        yield event.plain_result("🕙 正在拉取最新发布...")
        limit = self.config.get("fresh_limit", 60)
        topics = await self._fetch_all_pages(f"{self.base_url}/latest.json?order=created", limit)
        if not topics:
            yield event.plain_result("暂无数据。")
            return
        nodes = self._create_forward_nodes(event, topics, "🕙 最新发布")
        yield event.chain_result([Forward(id=int(time.time()), nodes=nodes)])

    async def _fetch_all_pages(self, base_api_url, limit):
        all_topics = []
        page = 0
        sep = "&" if "?" in base_api_url else "?"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                while len(all_topics) < limit:
                    url = f"{base_api_url}{sep}page={page}"
                    resp = await s.get(url, timeout=20)
                    if resp.status_code != 200: break
                    data = resp.json()
                    topics = data.get('topic_list', {}).get('topics', [])
                    if not topics: break
                    
                    # 过滤置顶逻辑
                    filter_pinned = self.config.get("filter_pinned", True)
                    filtered = [t for t in topics if not (filter_pinned and (t.get('pinned') or t.get('pinned_globally')))]
                    
                    all_topics.extend(filtered)
                    if len(all_topics) >= limit or len(topics) < 20: break
                    page += 1
                    await asyncio.sleep(0.3)
            return all_topics[:limit]
        except Exception:
            return all_topics[:limit] if all_topics else []

    def _create_forward_nodes(self, event, items, title_prefix):
        '''每 60 个话题打包成一个 Node，解决字数上限问题'''
        nodes = []
        bot_id = getattr(event, 'bot_id', '0')
        try: uin = int(bot_id)
        except: uin = 0
        show_author = self.config.get("show_author", True)
        
        chunk_size = 60 
        for i in range(0, len(items), chunk_size):
            chunk = items[i:i+chunk_size]
            full_text = f"{title_prefix} (第 {i+1}-{i+len(chunk)} 条 / 共 {len(items)} 条)\n" + "━" * 15 + "\n\n"
            for j, t in enumerate(chunk):
                idx = i + j + 1
                author_info = f" (作者: {t.get('last_poster_username')})" if show_author and t.get('last_poster_username') else ""
                full_text += f"{idx}. {t.get('title')}{author_info}\n🔗 {self.base_url}/t/{t.get('id')}\n\n"
            
            nodes.append(Node(
                id=int(time.time()) + i,
                uin=uin, 
                name="LINUX DO 助手", 
                content=[Plain(full_text.strip())]
            ))
        return nodes

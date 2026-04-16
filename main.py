from curl_cffi.requests import AsyncSession
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Node, Plain
from pydantic import BaseModel, Field # 增加 Pydantic 支持
import time

# 1. 定义配置类，AstrBot 会根据这个类自动生成 WebUI 界面
class LinuxDoConfig(BaseModel):
    top_limit: int = Field(default=15, description="每日热帖展示数量 (1-50)", ge=1, le=50)
    new_limit: int = int = Field(default=20, description="最新讨论展示数量 (1-50)", ge=1, le=50)
    search_limit: int = Field(default=10, description="搜索结果展示数量 (1-20)", ge=1, le=20)
    filter_pinned: bool = Field(default=True, description="是否过滤置顶帖 (Pinned Topics)")
    show_author: bool = Field(default=True, description="是否在列表中显示最后回帖人")

@register("linuxdo", "GeminiCLI", "LINUX DO 社区助手插件", "1.3.2")
class LinuxDoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.base_url = "https://linux.do"
        # 2. 正确加载并校验配置对象
        self.config = self.context.get_config().get("linuxdo", {})

    @filter.command("ld_top")
    async def get_top_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 全部热门话题 (配置化版)'''
        yield event.plain_result("🔍 正在拉取并打包全部热门话题...")
        
        # 3. 通过配置对象读取
        limit = self.config.get("top_limit", 15)
        url = f"{self.base_url}/top.json?period=daily"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=20)
                resp.raise_for_status()
                data = resp.json()
                
                topics = data.get('topic_list', {}).get('topics', [])
                topics = self._filter_topics(topics, limit)
                
                if not topics:
                    yield event.plain_result("暂时没有找到话题。")
                    return
                
                nodes = self._create_single_forward_node(event, topics, "🔥 热门话题")
                yield event.chain_result(nodes)
        except Exception as e:
            yield event.plain_result(f"❌ 获取失败: {str(e)}")

    @filter.command("ld_new")
    async def get_latest_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 最新帖子 (配置化版)'''
        yield event.plain_result("✨ 正在拉取并打包最新讨论...")
        
        limit = self.config.get("new_limit", 20)
        url = f"{self.base_url}/latest.json"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                
                topics = data.get('topic_list', {}).get('topics', [])
                topics = self._filter_topics(topics, limit)
                
                if not topics:
                    yield event.plain_result("暂时没有找到最新讨论。")
                    return
                
                nodes = self._create_single_forward_node(event, topics, "✨ 最新讨论")
                yield event.chain_result(nodes)
        except Exception as e:
            yield event.plain_result(f"❌ 获取失败: {str(e)}")

    @filter.command("ld")
    async def search_topics(self, event: AstrMessageEvent):
        '''搜索 LINUX DO 帖子 (配置化版)'''
        msg = event.message_str.strip()
        parts = msg.split()
        if len(parts) < 2:
            yield event.plain_result("请输入搜索关键词，例如: /ld 始皇")
            return
            
        keyword = parts[1]
        limit = self.config.get("search_limit", 10)
        yield event.plain_result(f"🔎 正在生成关于 '{keyword}' 的搜索结果...")
        
        url = f"{self.base_url}/search.json?q={keyword}"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                
                posts = data.get('posts', [])[:limit]
                if not posts:
                    yield event.plain_result(f"未找到与 '{keyword}' 相关的帖子。")
                    return
                
                search_topics = [{"title": p.get('topic_title'), "id": p.get('topic_id')} for p in posts]
                nodes = self._create_single_forward_node(event, search_topics, f"💡 搜索结果 '{keyword}'")
                yield event.chain_result(nodes)
        except Exception as e:
            yield event.plain_result(f"❌ 搜索出错: {str(e)}")

    def _filter_topics(self, topics, limit):
        '''根据配置过滤置顶帖并截取数量'''
        filter_pinned = self.config.get("filter_pinned", True)
        
        filtered = []
        for t in topics:
            if filter_pinned and (t.get('pinned') or t.get('pinned_globally')):
                continue
            filtered.append(t)
            
        return filtered[:limit]

    def _create_single_forward_node(self, event, items, title_prefix):
        '''将所有项打包进单一 Node 节点的工具'''
        bot_id = getattr(event, 'bot_id', '0')
        try: uin = int(bot_id)
        except: uin = 0
        
        show_author = self.config.get("show_author", True)
        full_text = f"{title_prefix} (共 {len(items)} 条)\n" + "━" * 15 + "\n\n"
        
        for i, t in enumerate(items):
            author_info = f" - @{t.get('last_poster_username')}" if show_author and t.get('last_poster_username') else ""
            full_text += f"{i+1}. {t.get('title')}{author_info}\n🔗 {self.base_url}/t/{t.get('id')}\n\n"
        
        return [Node(
            uin=uin,
            name="LINUX DO 助手",
            content=[Plain(full_text.strip())]
        )]

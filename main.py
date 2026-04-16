from curl_cffi.requests import AsyncSession
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Node, Plain
import time

@register("linuxdo", "GeminiCLI", "LINUX DO 社区助手插件", "1.2.0")
class LinuxDoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.base_url = "https://linux.do"

    @filter.command("ld_top")
    async def get_top_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 全部热门话题 (全量版)'''
        yield event.plain_result("🔍 正在拉取并生成全部热门话题...")
        
        url = f"{self.base_url}/top.json?period=daily"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=20)
                resp.raise_for_status()
                data = resp.json()
                
                topics = data.get('topic_list', {}).get('topics', [])
                if not topics:
                    yield event.plain_result("暂时没有找到热门话题。")
                    return
                
                nodes = self._create_forward_nodes(event, topics, "🔥 热门话题")
                yield event.chain_result(nodes)
                
        except Exception as e:
            yield event.plain_result(f"❌ 获取失败: {str(e)}")

    @filter.command("ld_new")
    async def get_latest_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 最新帖子'''
        yield event.plain_result("✨ 正在拉取 LINUX DO 最新讨论...")
        
        url = f"{self.base_url}/latest.json"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                
                topics = data.get('topic_list', {}).get('topics', [])
                if not topics:
                    yield event.plain_result("暂时没有找到最新帖子。")
                    return
                
                nodes = self._create_forward_nodes(event, topics, "✨ 最新讨论")
                yield event.chain_result(nodes)
        except Exception as e:
            yield event.plain_result(f"❌ 获取失败: {str(e)}")

    @filter.command("ld")
    async def search_topics(self, event: AstrMessageEvent):
        '''搜索 LINUX DO 帖子'''
        msg = event.get_plain_text().strip()
        parts = msg.split()
        if len(parts) < 2:
            yield event.plain_result("请输入搜索关键词，例如: /ld 始皇")
            return
            
        keyword = parts[1]
        yield event.plain_result(f"🔎 正在生成关于 '{keyword}' 的搜索结果...")
        
        url = f"{self.base_url}/search.json?q={keyword}"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                
                posts = data.get('posts', [])
                if not posts:
                    yield event.plain_result(f"未找到与 '{keyword}' 相关的帖子。")
                    return
                
                # 搜索结果稍微精简一些，提取标题和 ID
                search_topics = [{"title": p.get('topic_title'), "id": p.get('topic_id')} for p in posts]
                nodes = self._create_forward_nodes(event, search_topics, f"💡 搜索结果 '{keyword}'")
                yield event.chain_result(nodes)
        except Exception as e:
            yield event.plain_result(f"❌ 搜索出错: {str(e)}")

    def _create_forward_nodes(self, event, items, title_prefix):
        '''通用分块节点创建工具'''
        nodes = []
        self_id = event.get_self_id()
        try: uin = int(self_id)
        except: uin = 0
        
        chunk_size = 15 # 每 15 个分一块，保证在大部分适配器下展示美观且不超时
        for i in range(0, len(items), chunk_size):
            chunk = items[i:i + chunk_size]
            chunk_text = f"{title_prefix} ({i+1} - {i+len(chunk)})\n" + "━" * 15 + "\n"
            for j, t in enumerate(chunk):
                idx = i + j + 1
                chunk_text += f"{idx}. {t.get('title')}\n🔗 {self.base_url}/t/{t.get('id')}\n\n"
            
            nodes.append(Node(
                uin=uin,
                name="LINUX DO 助手",
                content=[Plain(chunk_text.strip())]
            ))
        return nodes

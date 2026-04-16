from curl_cffi.requests import AsyncSession
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Node, Plain
import time

@register("linuxdo", "GeminiCLI", "LINUX DO 社区助手插件", "1.2.2")
class LinuxDoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.base_url = "https://linux.do"

    @filter.command("ld_top")
    async def get_top_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 全部热门话题 (API 修正版)'''
        yield event.plain_result("🔍 正在拉取并打包全部热门话题...")
        
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
                
                nodes = self._create_single_forward_node(event, topics, "🔥 热门话题")
                yield event.chain_result(nodes)
                
        except Exception as e:
            yield event.plain_result(f"❌ 获取失败: {str(e)}")

    @filter.command("ld_new")
    async def get_latest_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 最新帖子 (API 修正版)'''
        yield event.plain_result("✨ 正在拉取并打包最新讨论...")
        
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
                
                nodes = self._create_single_forward_node(event, topics, "✨ 最新讨论")
                yield event.chain_result(nodes)
        except Exception as e:
            yield event.plain_result(f"❌ 获取失败: {str(e)}")

    @filter.command("ld")
    async def search_topics(self, event: AstrMessageEvent):
        '''搜索 LINUX DO 帖子 (API 修正版)'''
        # 修正：使用 event.message_str 获取原始消息字符串
        msg = event.message_str.strip()
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
                
                search_topics = [{"title": p.get('topic_title'), "id": p.get('topic_id')} for p in posts]
                nodes = self._create_single_forward_node(event, search_topics, f"💡 搜索结果 '{keyword}'")
                yield event.chain_result(nodes)
        except Exception as e:
            yield event.plain_result(f"❌ 搜索出错: {str(e)}")

    def _create_single_forward_node(self, event, items, title_prefix):
        '''将所有项打包进单一 Node 节点的工具'''
        # 修正：使用 event.self_id 获取机器人账号
        self_id = event.self_id
        try: uin = int(self_id)
        except: uin = 0
        
        full_text = f"{title_prefix} (共 {len(items)} 条)\n" + "━" * 15 + "\n\n"
        for i, t in enumerate(items):
            full_text += f"{i+1}. {t.get('title')}\n🔗 {self.base_url}/t/{t.get('id')}\n\n"
        
        return [Node(
            uin=uin,
            name="LINUX DO 助手",
            content=[Plain(full_text.strip())]
        )]

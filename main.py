from curl_cffi.requests import AsyncSession
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Node, Plain

@register("linuxdo", "GeminiCLI", "LINUX DO 社区助手插件", "1.1.4")
class LinuxDoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.base_url = "https://linux.do"

    @filter.command("ld_top")
    async def get_top_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 全部热门话题 (单节点极致版)'''
        yield event.plain_result("🔍 正在拉取并生成折叠消息...")
        
        url = f"{self.base_url}/top.json?period=daily"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                
                topics = data.get('topic_list', {}).get('topics', [])[:40]
                if not topics:
                    yield event.plain_result("暂时没有找到热门话题。")
                    return
                
                # 构造全部内容
                full_content = "🔥 LINUX DO 今日热榜 (Top 40)\n" + "━" * 15 + "\n\n"
                for i, t in enumerate(topics):
                    full_content += f"{i+1}. {t.get('title')}\n🔗 {self.base_url}/t/{t.get('id')}\n\n"
                
                self_id = event.get_self_id()
                try: uin = int(self_id)
                except: uin = 0
                
                # 创建唯一一个 Node，保证极致性能
                nodes = [Node(
                    uin=uin,
                    name="LINUX DO 助手",
                    content=[Plain(full_content.strip())]
                )]
                
                # 直接发送 Node 列表，实现单一气泡转发
                yield event.chain_result(nodes)
                
        except Exception as e:
            yield event.plain_result(f"❌ 获取失败: {str(e)}")

    @filter.command("ld")
    async def search_topics(self, event: AstrMessageEvent):
        '''搜索 LINUX DO 帖子 (单节点极致版)'''
        msg = event.get_plain_text().strip()
        parts = msg.split()
        if len(parts) < 2:
            yield event.plain_result("请输入搜索关键词，例如: /ld 始皇")
            return
            
        keyword = parts[1]
        yield event.plain_result(f"🔎 正在生成关于 '{keyword}' 的折叠结果...")
        
        url = f"{self.base_url}/search.json?q={keyword}"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                
                posts = data.get('posts', [])[:30]
                if not posts:
                    yield event.plain_result(f"未找到与 '{keyword}' 相关的帖子。")
                    return
                
                full_content = f"💡 关于 '{keyword}' 的搜索结果：\n" + "━" * 15 + "\n\n"
                for i, p in enumerate(posts):
                    full_content += f"{i+1}. {p.get('topic_title')}\n🔗 {self.base_url}/t/{p.get('topic_id')}\n\n"
                
                nodes = [Node(
                    uin=event.get_self_id(),
                    name="LINUX DO 搜索",
                    content=[Plain(full_content.strip())]
                )]
                
                yield event.chain_result(nodes)

        except Exception as e:
            yield event.plain_result(f"❌ 搜索出错: {str(e)}")

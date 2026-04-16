from curl_cffi.requests import AsyncSession
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp
import time

@register("linuxdo", "GeminiCLI", "LINUX DO 社区助手插件", "1.0.8")
class LinuxDoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.base_url = "https://linux.do"

    @filter.command("ld_top")
    async def get_top_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 今日热帖 (轻量化折叠版)'''
        yield event.plain_result("🔍 正在拉取并打包热门话题...")
        
        url = f"{self.base_url}/top.json?period=daily"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                
                topics = data.get('topic_list', {}).get('topics', [])[:15]
                if not topics:
                    yield event.plain_result("暂时没有找到热门话题。")
                    return
                
                # 将所有内容拼接成一段长文本，放入单个节点中
                full_content = "🔥 LINUX DO 今日热榜 (Top 15)\n" + "━" * 15 + "\n\n"
                for i, t in enumerate(topics):
                    full_content += f"{i+1}. {t.get('title')}\n🔗 {self.base_url}/t/{t.get('id')}\n\n"
                
                now = int(time.time())
                # 只构造一个节点，极大减轻适配器压力，防止超时
                single_node = Comp.Node(
                    id=now,
                    name="LINUX DO 助手",
                    uin=event.get_self_id(),
                    content=[Comp.Plain(full_content.strip())]
                )
                
                try:
                    yield event.chain_result([
                        Comp.Forward(
                            id=now + 1,
                            nodes=[single_node]
                        )
                    ])
                except Exception:
                    # 如果折叠消息还是发不出，直接发送文本
                    yield event.plain_result(full_content.strip())
                
        except Exception as e:
            yield event.plain_result(f"❌ 获取失败: {str(e)}")

    @filter.command("ld")
    async def search_topics(self, event: AstrMessageEvent):
        '''搜索 LINUX DO 帖子 (轻量化折叠版)'''
        msg = event.get_plain_text().strip()
        parts = msg.split()
        if len(parts) < 2:
            yield event.plain_result("请输入搜索关键词，例如: /ld 始皇")
            return
            
        keyword = parts[1]
        yield event.plain_result(f"🔎 正在搜索并打包关于 '{keyword}' 的结果...")
        
        url = f"{self.base_url}/search.json?q={keyword}"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                
                posts = data.get('posts', [])[:10]
                if not posts:
                    yield event.plain_result(f"未找到与 '{keyword}' 相关的帖子。")
                    return
                
                full_content = f"💡 关于 '{keyword}' 的搜索结果：\n" + "━" * 15 + "\n\n"
                for i, p in enumerate(posts):
                    full_content += f"{i+1}. {p.get('topic_title')}\n🔗 {self.base_url}/t/{p.get('topic_id')}\n\n"
                
                now = int(time.time())
                single_node = Comp.Node(
                    id=now,
                    name="LINUX DO 搜索",
                    uin=event.get_self_id(),
                    content=[Comp.Plain(full_content.strip())]
                )
                
                try:
                    yield event.chain_result([
                        Comp.Forward(
                            id=now + 1,
                            nodes=[single_node]
                        )
                    ])
                except Exception:
                    yield event.plain_result(full_content.strip())

        except Exception as e:
            yield event.plain_result(f"❌ 搜索出错: {str(e)}")

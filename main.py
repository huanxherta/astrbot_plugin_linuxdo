from curl_cffi.requests import AsyncSession
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp
import time

@register("linuxdo", "GeminiCLI", "LINUX DO 社区助手插件", "1.1.3")
class LinuxDoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.base_url = "https://linux.do"

    @filter.command("ld_top")
    async def get_top_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 全部热门话题 (分块打包防超时版)'''
        yield event.plain_result("🔍 正在拉取并安全打包热门话题...")
        
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
                
                nodes = []
                self_id = event.get_self_id()
                try: uin = int(self_id)
                except: uin = 0
                now = int(time.time())
                
                # 分块逻辑：每 8 个话题合为一个节点，总共约 5 个节点
                # 这能保证在单一气泡内有层次感，同时绝不超时
                chunk_size = 8
                for i in range(0, len(topics), chunk_size):
                    chunk = topics[i:i + chunk_size]
                    chunk_text = f"🔥 热门话题 ({i+1} - {i+len(chunk)})\n" + "━" * 15 + "\n"
                    for j, t in enumerate(chunk):
                        idx = i + j + 1
                        chunk_text += f"{idx}. {t.get('title')}\n🔗 {self.base_url}/t/{t.get('id')}\n\n"
                    
                    nodes.append(Comp.Node(
                        id=now + i,
                        uin=uin,
                        name="LINUX DO 助手",
                        content=[Comp.Plain(chunk_text.strip())]
                    ))
                
                # 再次尝试发送单一气泡
                try:
                    yield event.chain_result([
                        Comp.Forward(
                            id=now + 500, 
                            nodes=nodes
                        )
                    ])
                except Exception:
                    # 极速降级方案
                    yield event.plain_result("⚠️ 转发失败，已降级为长文本发送。")
                    full_text = ""
                    for i, t in enumerate(topics):
                        full_text += f"{i+1}. {t.get('title')} ({self.base_url}/t/{t.get('id')})\n"
                    yield event.plain_result(full_text.strip())
                
        except Exception as e:
            yield event.plain_result(f"❌ 获取失败: {str(e)}")

    @filter.command("ld")
    async def search_topics(self, event: AstrMessageEvent):
        '''搜索 LINUX DO 帖子 (分块打包防超时版)'''
        msg = event.get_plain_text().strip()
        parts = msg.split()
        if len(parts) < 2:
            yield event.plain_result("请输入搜索关键词，例如: /ld 始皇")
            return
            
        keyword = parts[1]
        yield event.plain_result(f"🔎 正在安全打包关于 '{keyword}' 的结果...")
        
        url = f"{self.base_url}/search.json?q={keyword}"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                
                posts = data.get('posts', [])[:24]
                if not posts:
                    yield event.plain_result(f"未找到与 '{keyword}' 相关的帖子。")
                    return
                
                nodes = []
                self_id = event.get_self_id()
                try: uin = int(self_id)
                except: uin = 0
                now = int(time.time())

                chunk_size = 6
                for i in range(0, len(posts), chunk_size):
                    chunk = posts[i:i + chunk_size]
                    chunk_text = f"💡 搜索结果 ({i+1} - {i+len(chunk)})\n" + "━" * 15 + "\n"
                    for j, p in enumerate(chunk):
                        idx = i + j + 1
                        chunk_text += f"{idx}. {p.get('topic_title')}\n🔗 {self.base_url}/t/{p.get('topic_id')}\n\n"
                    
                    nodes.append(Comp.Node(
                        id=now + i,
                        uin=uin,
                        name="LINUX DO 搜索",
                        content=[Comp.Plain(chunk_text.strip())]
                    ))
                
                yield event.chain_result([
                    Comp.Forward(
                        id=now + 500,
                        nodes=nodes
                    )
                ])

        except Exception as e:
            yield event.plain_result(f"❌ 搜索出错: {str(e)}")

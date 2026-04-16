from curl_cffi.requests import AsyncSession
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp
import time
import uuid

@register("linuxdo", "GeminiCLI", "LINUX DO 社区助手插件", "1.0.5")
class LinuxDoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.base_url = "https://linux.do"

    @filter.command("ld_top")
    async def get_top_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 今日热帖 (优化合并转发)'''
        yield event.plain_result("🔍 正在拉取 LINUX DO 热门话题...")
        
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
                
                nodes = []
                self_id = event.get_self_id()
                
                for i, t in enumerate(topics):
                    title = t.get('title')
                    t_id = t.get('id')
                    author = t.get('last_poster_username', '社区成员')
                    link = f"{self.base_url}/t/{t_id}"
                    
                    # 紧凑格式：1. 标题 - @作者
                    content = f"{i+1}. {title} - @{author}\n🔗 {link}"
                    
                    nodes.append(Comp.Node(
                        id=str(uuid.uuid4()), # 使用 UUID 确保唯一性
                        name="LINUX DO 热帖",
                        uin=self_id,
                        content=[Comp.Plain(content)]
                    ))
                
                try:
                    # 修复关键：为 Forward 组件本身添加 id
                    yield event.chain_result([
                        Comp.Forward(
                            id=str(uuid.uuid4()), 
                            nodes=nodes
                        )
                    ])
                except Exception:
                    # 如果合并转发失败（如平台不支持），发送极致压缩的文本
                    result = "🔥 LINUX DO 今日热榜 (Top 15)\n" + "-"*20 + "\n"
                    for i, t in enumerate(topics):
                        # 一帖一行链接模式，极大缩小长度
                        result += f"{i+1}. {t.get('title')} ({self.base_url}/t/{t.get('id')})\n"
                    yield event.plain_result(result.strip())
                
        except Exception as e:
            yield event.plain_result(f"❌ 获取失败: {str(e)}")

    @filter.command("ld")
    async def search_topics(self, event: AstrMessageEvent):
        '''搜索 LINUX DO 帖子 (优化展示)'''
        msg = event.get_plain_text().strip()
        parts = msg.split()
        if len(parts) < 2:
            yield event.plain_result("请输入搜索关键词，例如: /ld 始皇")
            return
            
        keyword = parts[1]
        yield event.plain_result(f"🔎 正在搜索关于 '{keyword}' 的结果...")
        
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
                
                nodes = []
                self_id = event.get_self_id()
                for i, p in enumerate(posts):
                    title = p.get('topic_title', '无标题')
                    t_id = p.get('topic_id')
                    link = f"{self.base_url}/t/{t_id}"
                    
                    content = f"📌 {title}\n🔗 {link}"
                    
                    nodes.append(Comp.Node(
                        id=str(uuid.uuid4()),
                        name="LINUX DO 搜索",
                        uin=self_id,
                        content=[Comp.Plain(content)]
                    ))
                
                try:
                    yield event.chain_result([
                        Comp.Forward(
                            id=str(uuid.uuid4()),
                            nodes=nodes
                        )
                    ])
                except Exception:
                    result = f"💡 关于 '{keyword}' 的搜索结果：\n" + "-"*20 + "\n"
                    for p in posts:
                        result += f"📌 {p.get('topic_title')} ({self.base_url}/t/{p.get('topic_id')})\n"
                    yield event.plain_result(result.strip())

        except Exception as e:
            yield event.plain_result(f"❌ 搜索出错: {str(e)}")

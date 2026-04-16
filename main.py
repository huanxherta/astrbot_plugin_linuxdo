from curl_cffi.requests import AsyncSession
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp
import time

@register("linuxdo", "GeminiCLI", "LINUX DO 社区助手插件", "1.0.4")
class LinuxDoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.base_url = "https://linux.do"

    @filter.command("ld_top")
    async def get_top_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 今日热帖 (修正合并转发版)'''
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
                
                # 每一个节点添加必需的字段，参考 OneBot 规范
                for i, t in enumerate(topics):
                    title = t.get('title')
                    slug = t.get('slug')
                    t_id = t.get('id')
                    author = t.get('last_poster_username', '社区成员')
                    
                    content = f"{i+1}. {title}\n👤 最后回复: {author}\n🔗 {self.base_url}/t/{slug}/{t_id}"
                    
                    # 修正 Node 构造，确保包含所有必需字段
                    nodes.append(Comp.Node(
                        id=str(int(time.time() * 1000) + i), # 增加唯一 ID
                        name="LINUX DO 热帖",
                        uin=self_id,
                        content=[Comp.Plain(content)]
                    ))
                
                # 如果 Forward 还是校验失败，我们退而求其次使用长文本
                try:
                    yield event.chain_result([Comp.Forward(nodes=nodes)])
                except Exception:
                    # 备选方案：如果合并转发在当前平台不可用，直接发长文本
                    long_text = "🔥 LINUX DO 今日热榜 (Top 15)\n\n"
                    for i, t in enumerate(topics):
                        long_text += f"{i+1}. {t.get('title')}\n🔗 {self.base_url}/t/{t.get('id')}\n\n"
                    yield event.plain_result(long_text.strip())
                
        except Exception as e:
            yield event.plain_result(f"❌ 获取失败: {str(e)}")

    @filter.command("ld")
    async def search_topics(self, event: AstrMessageEvent):
        '''搜索 LINUX DO 帖子: /ld <关键词> (修正合并转发版)'''
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
                    excerpt = p.get('blurb', '').replace("\n", " ")
                    
                    content = f"📌 {title}\n📝 摘要: {excerpt}...\n🔗 {self.base_url}/t/{t_id}"
                    
                    nodes.append(Comp.Node(
                        id=str(int(time.time() * 1001) + i),
                        name="LINUX DO 搜索",
                        uin=self_id,
                        content=[Comp.Plain(content)]
                    ))
                
                try:
                    yield event.chain_result([Comp.Forward(nodes=nodes)])
                except Exception:
                    long_text = f"💡 关于 '{keyword}' 的搜索结果：\n\n"
                    for p in posts:
                        long_text += f"📌 {p.get('topic_title')}\n🔗 {self.base_url}/t/{p.get('topic_id')}\n\n"
                    yield event.plain_result(long_text.strip())

        except Exception as e:
            yield event.plain_result(f"❌ 搜索出错: {str(e)}")

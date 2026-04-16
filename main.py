from curl_cffi.requests import AsyncSession
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp
import time

@register("linuxdo", "GeminiCLI", "LINUX DO 社区助手插件", "1.1.2")
class LinuxDoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.base_url = "https://linux.do"

    @filter.command("ld_top")
    async def get_top_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 全部热门话题 (真正的单一气泡合并转发)'''
        yield event.plain_result("🔍 正在拉取并打包全部热门话题...")
        
        url = f"{self.base_url}/top.json?period=daily"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                
                topics = data.get('topic_list', {}).get('topics', [])[:40] # 限制前 40 个，防止节点过多
                if not topics:
                    yield event.plain_result("暂时没有找到热门话题。")
                    return
                
                nodes = []
                self_id = event.get_self_id()
                try: uin = int(self_id)
                except: uin = 0
                
                now = int(time.time())
                
                # 创建标题节点
                nodes.append(Comp.Node(
                    id=now,
                    uin=uin,
                    name="LINUX DO 助手",
                    content=[Comp.Plain(f"🔥 今日共有 {len(topics)} 条热门话题：")]
                ))

                # 为每个话题创建 Node
                for i, t in enumerate(topics):
                    title = t.get('title')
                    t_id = t.get('id')
                    author = t.get('last_poster_username', '社区成员')
                    content = f"{i+1}. {title}\n👤 最后回复: {author}\n🔗 {self.base_url}/t/{t_id}"
                    
                    nodes.append(Comp.Node(
                        id=now + i + 1,
                        uin=uin,
                        name="LINUX DO 热帖",
                        content=[Comp.Plain(content)]
                    ))
                
                # 关键：只发送一个包含所有 nodes 的 Forward 对象
                # 这样在群里只会看到一个气泡
                yield event.chain_result([
                    Comp.Forward(
                        id=now + 100, 
                        nodes=nodes
                    )
                ])
                
        except Exception as e:
            yield event.plain_result(f"❌ 获取失败: {str(e)}")

    @filter.command("ld")
    async def search_topics(self, event: AstrMessageEvent):
        '''搜索 LINUX DO 帖子 (真正的单一气泡合并转发)'''
        msg = event.get_plain_text().strip()
        parts = msg.split()
        if len(parts) < 2:
            yield event.plain_result("请输入搜索关键词，例如: /ld 始皇")
            return
            
        keyword = parts[1]
        yield event.plain_result(f"🔎 正在搜索关于 '{keyword}' 的全部结果...")
        
        url = f"{self.base_url}/search.json?q={keyword}"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                
                posts = data.get('posts', [])[:30] # 搜索结果限制前 30 个
                if not posts:
                    yield event.plain_result(f"未找到与 '{keyword}' 相关的帖子。")
                    return
                
                nodes = []
                self_id = event.get_self_id()
                try: uin = int(self_id)
                except: uin = 0

                now = int(time.time())
                nodes.append(Comp.Node(
                    id=now,
                    uin=uin,
                    name="LINUX DO 搜索",
                    content=[Comp.Plain(f"💡 找到 {len(posts)} 条关于 '{keyword}' 的结果：")]
                ))

                for i, p in enumerate(posts):
                    title = p.get('topic_title', '无标题')
                    t_id = p.get('topic_id')
                    link = f"{self.base_url}/t/{t_id}"
                    content = f"📌 {title}\n🔗 {link}"
                    
                    nodes.append(Comp.Node(
                        id=now + i + 1,
                        uin=uin,
                        name="搜索结果",
                        content=[Comp.Plain(content)]
                    ))
                
                # 只发送一个 Forward 对象
                yield event.chain_result([
                    Comp.Forward(
                        id=now + 100,
                        nodes=nodes
                    )
                ])

        except Exception as e:
            yield event.plain_result(f"❌ 搜索出错: {str(e)}")

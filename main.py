from curl_cffi.requests import AsyncSession
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp

@register("linuxdo", "GeminiCLI", "LINUX DO 社区助手插件", "1.0.3")
class LinuxDoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.base_url = "https://linux.do"

    @filter.command("ld_top")
    async def get_top_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 今日热帖 (合并转发版)'''
        yield event.plain_result("🔍 正在拉取 LINUX DO 热门话题并打包...")
        
        url = f"{self.base_url}/top.json?period=daily"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                
                topics = data.get('topic_list', {}).get('topics', [])[:15] # 数量增加到 15 个
                if not topics:
                    yield event.plain_result("暂时没有找到热门话题。")
                    return
                
                # 构造合并转发节点列表
                nodes = []
                
                # 头部说明
                header_node = Comp.Node(
                    content=[Comp.Plain("🔥 LINUX DO 今日热榜 (Top 15)")],
                    name="LINUX DO 助手",
                    uin=event.get_self_id()
                )
                nodes.append(header_node)

                for i, t in enumerate(topics):
                    title = t.get('title')
                    slug = t.get('slug')
                    t_id = t.get('id')
                    author = t.get('last_poster_username', '社区成员')
                    
                    content = f"{i+1}. {title}\n👤 最后回复: {author}\n🔗 {self.base_url}/t/{slug}/{t_id}"
                    
                    # 将每一个话题作为一个转发节点
                    node = Comp.Node(
                        content=[Comp.Plain(content)],
                        name="LINUX DO 热帖",
                        uin=event.get_self_id()
                    )
                    nodes.append(node)
                
                # 发送合并转发消息
                yield event.chain_result([Comp.Forward(nodes=nodes)])
                
        except Exception as e:
            yield event.plain_result(f"❌ 获取失败: {str(e)}")

    @filter.command("ld")
    async def search_topics(self, event: AstrMessageEvent):
        '''搜索 LINUX DO 帖子: /ld <关键词> (合并转发版)'''
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
                
                posts = data.get('posts', [])[:10] # 搜索结果增加到 10 个
                if not posts:
                    yield event.plain_result(f"未找到与 '{keyword}' 相关的帖子。")
                    return
                
                nodes = []
                for p in posts:
                    title = p.get('topic_title', '无标题')
                    t_id = p.get('topic_id')
                    excerpt = p.get('blurb', '').replace("\n", " ") # 提取摘要
                    
                    content = f"📌 {title}\n📝 摘要: {excerpt}...\n🔗 {self.base_url}/t/{t_id}"
                    
                    nodes.append(Comp.Node(
                        content=[Comp.Plain(content)],
                        name="搜索结果",
                        uin=event.get_self_id()
                    ))
                
                yield event.chain_result([Comp.Forward(nodes=nodes)])
        except Exception as e:
            yield event.plain_result(f"❌ 搜索出错: {str(e)}")

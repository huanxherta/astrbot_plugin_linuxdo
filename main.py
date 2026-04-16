from curl_cffi.requests import AsyncSession
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Node, Plain

@register("linuxdo", "GeminiCLI", "LINUX DO 社区助手插件", "1.1.5")
class LinuxDoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.base_url = "https://linux.do"

    @filter.command("ld_top")
    async def get_top_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 全部热门话题 (无上限版)'''
        yield event.plain_result("🔍 正在拉取并生成全部热门话题折叠消息...")
        
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
                
                nodes = []
                self_id = event.get_self_id()
                try: uin = int(self_id)
                except: uin = 0
                
                # 分块逻辑：每 50 个话题为一个节点，防止单节点文本超过 5000 字
                # 这也是为了兼容不同适配器对单条消息长度的限制
                chunk_size = 50
                for i in range(0, len(topics), chunk_size):
                    chunk = topics[i:i + chunk_size]
                    chunk_text = f"🔥 热门话题 ({i+1} - {i+len(chunk)})\n" + "━" * 15 + "\n"
                    for j, t in enumerate(chunk):
                        idx = i + j + 1
                        chunk_text += f"{idx}. {t.get('title')}\n🔗 {self.base_url}/t/{t.get('id')}\n\n"
                    
                    nodes.append(Node(
                        uin=uin,
                        name="LINUX DO 助手",
                        content=[Plain(chunk_text.strip())]
                    ))
                
                # 发送包含所有大块节点的合并转发列表
                yield event.chain_result(nodes)
                
        except Exception as e:
            yield event.plain_result(f"❌ 获取失败: {str(e)}")

    @filter.command("ld")
    async def search_topics(self, event: AstrMessageEvent):
        '''搜索 LINUX DO 帖子 (无上限版)'''
        msg = event.get_plain_text().strip()
        parts = msg.split()
        if len(parts) < 2:
            yield event.plain_result("请输入搜索关键词，例如: /ld 始皇")
            return
            
        keyword = parts[1]
        yield event.plain_result(f"🔎 正在生成关于 '{keyword}' 的全部结果...")
        
        url = f"{self.base_url}/search.json?q={keyword}"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=20)
                resp.raise_for_status()
                data = resp.json()
                
                posts = data.get('posts', [])
                if not posts:
                    yield event.plain_result(f"未找到与 '{keyword}' 相关的帖子。")
                    return
                
                nodes = []
                self_id = event.get_self_id()
                try: uin = int(self_id)
                except: uin = 0

                chunk_size = 40
                for i in range(0, len(posts), chunk_size):
                    chunk = posts[i:i + chunk_size]
                    chunk_text = f"💡 搜索结果 ({i+1} - {i+len(chunk)})\n" + "━" * 15 + "\n"
                    for j, p in enumerate(chunk):
                        idx = i + j + 1
                        chunk_text += f"{idx}. {p.get('topic_title')}\n🔗 {self.base_url}/t/{p.get('topic_id')}\n\n"
                    
                    nodes.append(Node(
                        uin=uin,
                        name="LINUX DO 搜索",
                        content=[Plain(chunk_text.strip())]
                    ))
                
                yield event.chain_result(nodes)

        except Exception as e:
            yield event.plain_result(f"❌ 搜索出错: {str(e)}")

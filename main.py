import httpx
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register

@register("linuxdo", "GeminiCLI", "LINUX DO 社区助手插件", "1.0.1")
class LinuxDoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.base_url = "https://linux.do"
        # 伪装成真实的浏览器，绕过基础的机器人检测
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }

    @filter.command("ld_top")
    async def get_top_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 今日热帖'''
        yield event.plain_result("🔍 正在拉取 LINUX DO 热门话题...")
        
        url = f"{self.base_url}/top.json?period=daily"
        try:
            async with httpx.AsyncClient(headers=self.headers) as client:
                resp = await client.get(url, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                
                topics = data.get('topic_list', {}).get('topics', [])[:5]
                if not topics:
                    yield event.plain_result("暂时没有找到热门话题。")
                    return
                
                result = "🔥 LINUX DO 今日热榜：\n"
                for i, t in enumerate(topics):
                    title = t.get('title')
                    slug = t.get('slug')
                    t_id = t.get('id')
                    result += f"{i+1}. {title}\n🔗 {self.base_url}/t/{slug}/{t_id}\n\n"
                
                yield event.plain_result(result.strip())
        except Exception as e:
            yield event.plain_result(f"❌ 获取失败: {str(e)}")

    @filter.command("ld")
    async def search_topics(self, event: AstrMessageEvent):
        '''搜索 LINUX DO 帖子: /ld <关键词>'''
        msg = event.get_plain_text().strip()
        parts = msg.split()
        if len(parts) < 2:
            yield event.plain_result("请输入搜索关键词，例如: /ld 始皇")
            return
            
        keyword = parts[1]
        yield event.plain_result(f"🔎 正在 LINUX DO 中搜索: {keyword}...")
        
        url = f"{self.base_url}/search.json?q={keyword}"
        try:
            async with httpx.AsyncClient(headers=self.headers) as client:
                resp = await client.get(url, timeout=10)
                resp.raise_for_status() # 确保状态码正常
                data = resp.json()
                
                posts = data.get('posts', [])[:5]
                if not posts:
                    yield event.plain_result(f"未找到与 '{keyword}' 相关的帖子。")
                    return
                
                result = f"💡 为您找到关于 '{keyword}' 的结果：\n\n"
                for p in posts:
                    title = p.get('topic_title', '无标题')
                    t_id = p.get('topic_id')
                    result += f"📌 {title}\n🔗 {self.base_url}/t/{t_id}\n\n"
                
                yield event.plain_result(result.strip())
        except Exception as e:
            yield event.plain_result(f"❌ 搜索出错: {str(e)}")

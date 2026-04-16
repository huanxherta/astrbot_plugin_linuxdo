from curl_cffi.requests import AsyncSession
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register

@register("linuxdo", "GeminiCLI", "LINUX DO 社区助手插件", "1.0.2")
class LinuxDoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.base_url = "https://linux.do"

    @filter.command("ld_top")
    async def get_top_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 今日热帖'''
        yield event.plain_result("🔍 正在拉取 LINUX DO 热门话题 (使用加密混淆绕过)...")
        
        url = f"{self.base_url}/top.json?period=daily"
        try:
            # 使用 curl_cffi 模拟 Chrome 浏览器的 TLS 指纹
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=15)
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
            yield event.plain_result(f"❌ 获取失败: {str(e)}\n提示: 请确保已安装 curl_cffi 依赖。")

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
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=15)
                resp.raise_for_status()
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

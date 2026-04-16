from curl_cffi.requests import AsyncSession
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register

@register("linuxdo", "GeminiCLI", "LINUX DO 社区助手插件", "1.0.7")
class LinuxDoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.base_url = "https://linux.do"

    @filter.command("ld_top")
    async def get_top_topics(self, event: AstrMessageEvent):
        '''获取 LINUX DO 今日热帖 (极简文本版)'''
        yield event.plain_result("🔍 正在拉取今日热门话题...")
        
        url = f"{self.base_url}/top.json?period=daily"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                
                topics = data.get('topic_list', {}).get('topics', [])[:10] # 数量设为 10 个以防过长
                if not topics:
                    yield event.plain_result("暂时没有找到热门话题。")
                    return
                
                result = "🔥 LINUX DO 今日热榜 (Top 10)\n" + "━" * 15 + "\n"
                for i, t in enumerate(topics):
                    title = t.get('title')
                    t_id = t.get('id')
                    # 极简模式：1. 标题\n   🔗 短链接
                    result += f"{i+1}. {title}\n🔗 {self.base_url}/t/{t_id}\n\n"
                
                yield event.plain_result(result.strip())
                
        except Exception as e:
            yield event.plain_result(f"❌ 获取失败: {str(e)}")

    @filter.command("ld")
    async def search_topics(self, event: AstrMessageEvent):
        '''搜索 LINUX DO 帖子 (极简文本版)'''
        msg = event.get_plain_text().strip()
        parts = msg.split()
        if len(parts) < 2:
            yield event.plain_result("请输入搜索关键词，例如: /ld 始皇")
            return
            
        keyword = parts[1]
        yield event.plain_result(f"🔎 正在搜索关于 '{keyword}' 的内容...")
        
        url = f"{self.base_url}/search.json?q={keyword}"
        try:
            async with AsyncSession(impersonate="chrome120") as s:
                resp = await s.get(url, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                
                posts = data.get('posts', [])[:8] # 搜索结果设为 8 个
                if not posts:
                    yield event.plain_result(f"未找到与 '{keyword}' 相关的帖子。")
                    return
                
                result = f"💡 关于 '{keyword}' 的搜索结果：\n" + "━" * 15 + "\n"
                for i, p in enumerate(posts):
                    title = p.get('topic_title', '无标题')
                    t_id = p.get('topic_id')
                    result += f"{i+1}. {title}\n🔗 {self.base_url}/t/{t_id}\n\n"
                
                yield event.plain_result(result.strip())
        except Exception as e:
            yield event.plain_result(f"❌ 搜索出错: {str(e)}")

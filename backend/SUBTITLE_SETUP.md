# AI 摘要功能 - 字幕配置指南

## 为什么需要 Cookie？

B站大多数视频的 AI 字幕需要登录后才能获取，yt-dlp 在 macOS 上无法自动解密 Chrome Cookie（v127+ 加密方式变更），因此需要手动导出 Cookie 文件。

---

## 方法一：导出 cookies.txt（推荐，支持所有平台）

### 步骤
1. 在 Chrome/Edge 安装扩展：
   - [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - 或 [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg)
2. 打开 **bilibili.com**，确保已登录
3. 点击扩展图标，选择「Export」导出为 Netscape 格式
4. 将文件保存为：`backend/cookies.txt`
5. 重启后端服务

### 验证
```bash
cd backend
cat cookies.txt | grep bilibili | head -5
```

---

## 方法二：配置 SESSDATA（仅 B站）

### 步骤
1. 在 Chrome 打开 bilibili.com，确保已登录
2. 按 F12 打开开发者工具 → Application → Cookies → bilibili.com
3. 找到 `SESSDATA` 字段，复制其 Value
4. 创建文件 `backend/bilibili_sessdata.txt`，粘贴 SESSDATA 值（一行）
5. 重启后端服务

### 示例
```
8a1b2c3d%2C1234567890%2C12345*ab
```

---

## 验证配置是否生效

```bash
curl http://localhost:8000/api/v2/subtitle-status
```

返回示例：
```json
{
  "has_cookies_file": true,
  "has_sessdata": false,
  "cookies_file_path": "/path/to/backend/cookies.txt",
  "sessdata_file_path": "/path/to/backend/bilibili_sessdata.txt"
}
```

---

## 支持的视频类型

| 平台 | 无配置 | 有 cookies.txt | 有 SESSDATA |
|------|--------|---------------|------------|
| B站（有手动字幕） | ✅ | ✅ | ✅ |
| B站（AI 字幕） | ❌ | ✅ | ✅ |
| YouTube（有 CC 字幕） | ✅ | ✅ | - |
| YouTube（自动字幕） | ✅ | ✅ | - |
| 其他平台 | 视情况 | ✅ | - |

---

## 常见问题

**Q: 配置了 cookies.txt 还是提示无字幕？**  
A: 确认该视频在 B站 App 或网页中播放器右下角有「字幕」按钮，无字幕按钮的视频确实没有字幕。

**Q: cookies.txt 多久失效？**  
A: B站 Cookie 通常有效期 6 个月，过期后重新导出即可。

**Q: 有没有不需要 Cookie 的视频？**  
A: YouTube 的 CC 字幕（非自动生成）、部分 B站 UP 主手动上传的字幕无需登录即可获取。

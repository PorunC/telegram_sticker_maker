# 🚀 部署指南

本项目支持多种云平台快速部署到公网。推荐使用以下平台：

## 📋 部署前准备

1. **获取Telegram Bot Token**:
   - 在Telegram中搜索 @BotFather
   - 创建新bot: `/newbot`
   - 记录Bot Token

2. **获取用户ID**:
   - 在Telegram中搜索 @userinfobot
   - 发送任意消息获取你的用户ID

## 🌟 推荐平台: Railway (免费)

### 特点
- ✅ 免费 $5/月额度
- ✅ 自动HTTPS
- ✅ 简单部署
- ✅ 支持环境变量

### 部署步骤
1. Fork或Clone此仓库到你的GitHub
2. 访问 [railway.app](https://railway.app)
3. 使用GitHub登录
4. 点击 "New Project" → "Deploy from GitHub repo"
5. 选择此项目仓库
6. 设置环境变量:
   - `TELEGRAM_BOT_TOKEN`: 你的Bot Token
   - `TELEGRAM_USER_ID`: 你的用户ID
7. 点击Deploy，等待部署完成
8. 获取公网URL，开始使用！

## 🔥 Render (免费)

### 特点  
- ✅ 免费tier
- ✅ 自动SSL
- ✅ GitHub集成
- ⚠️ 免费版会休眠

### 部署步骤
1. 访问 [render.com](https://render.com)
2. 连接GitHub账户
3. 选择此项目仓库
4. 选择 "Web Service"
5. 配置设置:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python start_web.py --port $PORT`
6. 添加环境变量
7. 点击"Create Web Service"

## ⚡ Vercel (免费)

### 特点
- ✅ 极速部署
- ✅ CDN加速  
- ✅ 自动HTTPS
- ⚠️ Serverless限制

### 部署步骤
1. 安装Vercel CLI: `npm i -g vercel`
2. 在项目目录运行: `vercel`
3. 按提示配置项目
4. 设置环境变量: `vercel env add`
5. 重新部署: `vercel --prod`

## 🐳 Docker部署

### 本地测试
```bash
# 构建镜像
docker build -t telegram-sticker-maker .

# 运行容器
docker run -p 8080:8080 \
  -e TELEGRAM_BOT_TOKEN="your_token" \
  -e TELEGRAM_USER_ID="your_id" \
  telegram-sticker-maker
```

### 部署到云平台
- **Google Cloud Run**
- **AWS ECS** 
- **Azure Container Instances**
- **DigitalOcean App Platform**

## 🔧 环境变量配置

必需变量:
- `TELEGRAM_BOT_TOKEN`: Telegram Bot令牌
- `TELEGRAM_USER_ID`: 你的Telegram用户ID

可选变量:
- `DEFAULT_EMOJI`: 默认emoji (默认: 😀)
- `PROXY_ENABLED`: 是否启用代理 (默认: false)
- `PROXY_TYPE`: 代理类型 (http/socks5/socks4)
- `PROXY_HOST`: 代理主机
- `PROXY_PORT`: 代理端口
- `PORT`: 服务端口 (默认: 5000)
- `FLASK_ENV`: Flask环境 (development/production)

## 📝 部署后配置

1. 访问你的应用URL
2. 进入"设置"页面
3. 填写Telegram Bot Token和用户ID
4. 配置代理(如需要)
5. 开始创建表情包！

## 🔍 故障排除

### 常见问题

**部署失败**:
- 检查requirements.txt是否正确
- 确认Python版本兼容性(3.7+)
- 查看构建日志错误信息

**FFmpeg错误**:
- 大多数云平台已预装FFmpeg
- 如缺失，使用Dockerfile部署

**内存不足**:
- 减少同时处理的文件数量
- 使用付费tier获得更多资源

**网络超时**:
- 配置代理设置
- 检查Telegram API访问权限

## 💡 优化建议

1. **生产部署**:
   - 设置 `FLASK_ENV=production`
   - 使用付费tier获得更好性能
   - 配置CDN加速静态文件

2. **安全建议**:
   - 定期轮换Bot Token
   - 限制用户访问权限
   - 监控API使用量

3. **监控运维**:
   - 设置健康检查
   - 配置日志收集
   - 监控资源使用

## 📞 技术支持

部署遇到问题？
- 查看项目Issues
- 检查平台官方文档
- 咨询社区论坛

---

🎉 祝你部署成功！享受制作Telegram表情包的乐趣！
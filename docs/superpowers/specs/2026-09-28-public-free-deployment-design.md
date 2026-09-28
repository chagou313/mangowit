# Mangowit 免费公开部署设计

日期：2026-09-28

## 目标

为 Mangowit 提供一个任何人都可以通过 HTTPS 链接访问的公开网站，同时在免费额度内长期保存用户账号、社区内容和用户头像。GitHub 仓库继续保持私有。

## 已确认的约束

- 使用免费方案。
- 可以接受免费网站服务闲置休眠，以及首次访问时的冷启动等待。
- 用户账号、登录相关数据、社区内容等关系数据必须持久保存。
- 用户上传的头像也应持久保存。
- 不把生产密钥、数据库连接字符串或云存储凭据提交到 GitHub。

## 方案选择

采用以下组合：

- Render 免费 Web Service：运行 Django 应用并提供公开的 `onrender.com` HTTPS 地址。
- Neon 免费 PostgreSQL：保存 Django 用户、会话、问答和社区数据。
- Cloudinary 免费账户：保存用户上传的头像并通过 HTTPS 提供图片。

选择该方案的原因是 Web 运行环境、关系数据库和上传文件各自承担单一职责。Render 免费实例的本地文件系统是临时的，因此不能保存 SQLite 数据库或用户上传文件；把数据和图片放到外部持久服务可以避免部署、重启和休眠造成的数据丢失。

## 应用架构

浏览器请求首先到达 Render 上的 Gunicorn/Django 服务。Django 使用 WhiteNoise 提供版本化静态资源，并通过环境变量连接 Neon PostgreSQL。注册、登录、社区发帖和问答数据写入 PostgreSQL。头像上传由 Django 校验后写入 Cloudinary，数据库只保存对应的云端资源标识或 URL。

本地开发继续默认使用 SQLite 和本地媒体目录，以免开发者必须创建云服务账号。只有在设置生产环境变量后，应用才切换到 PostgreSQL、Cloudinary、关闭调试模式并启用安全配置。

## 配置和代码变更

1. 增加生产依赖：Gunicorn、WhiteNoise、PostgreSQL 驱动、数据库 URL 解析和 Cloudinary Django 集成。
2. 扩展 Django 设置：
   - 存在 `DATABASE_URL` 时使用 PostgreSQL，否则使用现有 SQLite。
   - 存在 Cloudinary 配置时使用云端媒体存储，否则使用本地媒体目录。
   - 生产环境启用安全 Cookie、代理 HTTPS 头和非调试模式。
   - 使用 WhiteNoise 的压缩静态文件存储。
3. 增加 Render Blueprint 或等价部署配置，固定构建命令、启动命令、健康检查地址和所需环境变量。
4. 构建阶段安装依赖并执行 `collectstatic`；服务启动前执行数据库迁移，然后启动 Gunicorn。
5. 将示例 AI 问答导入逻辑改为可重复执行的管理命令。首次部署或数据为空时可安全导入，不产生重复记录。
6. 更新 README，记录本地 8001 端口启动方式、云端架构、部署步骤和环境变量名称。

## 数据迁移与初始化

当前本地 SQLite 包含一个本地用户和登录会话，这些内容不会上传到生产环境。生产数据库从空库开始执行 Django migrations，然后导入项目自带的 21 条示例 AI 问答。公开用户需要在网站上重新注册。

后续部署只运行幂等迁移和幂等示例数据命令，不删除或覆盖已有用户、社区帖子和头像记录。

## 图片上传

允许的头像文件继续由 Django 表单和 Pillow 校验。上传成功后才更新用户资料；Cloudinary 上传失败时显示明确错误并保留原头像。Cloudinary 密钥只保存在 Render 环境变量中。静态演示图片和现有视频仍作为版本化静态资源随应用发布，不占用用户上传空间。

## 错误处理

- 数据库暂时不可用时，请求返回通用服务错误，日志记录具体异常但不输出凭据。
- Cloudinary 暂时不可用时，头像更新失败但其他资料和原头像不受影响。
- 缺少生产必需环境变量时，部署应在启动阶段明确失败，而不是使用不安全的默认值上线。
- 健康检查只验证 Django 服务可响应，不写入数据。

## 验证方案

本地验证包括：

- 运行现有 Django 测试套件。
- 新增 SQLite 回退、`DATABASE_URL` 解析、生产安全设置和云媒体配置测试。
- 验证示例数据命令重复运行不会重复插入。
- 执行 `collectstatic` 和 Django deployment checks。

上线验证包括：

- 公开 HTTPS 首页、新闻、知识、问答和社区页面均返回成功响应。
- 新用户可以注册、退出后重新登录。
- 创建社区帖子后触发一次重新部署，确认帖子仍存在。
- 上传头像后触发一次重新部署，确认头像仍能显示。
- 核对 Render 日志中没有密钥或数据库连接字符串。

## 运维限制

Render 免费 Web Service 闲置后会休眠，首次访问可能等待约一分钟。免费额度和服务条款可能变化；如果流量或存储超过免费额度，需要升级或迁移。Neon 和 Cloudinary 的用量应定期检查。生产凭据需要在相应平台轮换，不能提交到仓库。

## 成功标准

- 获得一个可公开分享的 HTTPS 地址。
- 无需 GitHub 权限即可访问网站。
- 用户账号、帖子和头像在服务休眠、重启及重新部署后仍然存在。
- GitHub 中不包含生产密钥、本地数据库、登录会话或用户隐私数据。
- 自动化测试与上线验证全部通过。

## 参考资料

- Render 免费服务限制：https://render.com/docs/free
- Render Web Service：https://render.com/docs/web-services
- Neon 免费方案说明：https://neon.com/blog/how-to-make-the-most-of-neons-free-plan
- Cloudinary Django 上传文档：https://cloudinary.com/documentation/django_image_and_video_upload

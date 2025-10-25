# 🏪 星之梦手作管理系统

一个基于 Python Streamlit 开发的现代化手作管理系统，专为小型企业和个体经营者设计。集成了先进的缓存机制、性能监控、日志管理和数据库优化功能，提供企业级的稳定性和性能。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![SQLite](https://img.shields.io/badge/SQLite-3.0+-green.svg)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 功能特色

### 📊 仪表板
- 业务数据概览
- 关键指标展示
- 订单趋势分析
- 库存预警提醒

### 👥 客户管理
- 客户信息 CRUD 操作
- 积分系统管理
- 客户搜索功能
- 历史订单追踪

### 🧵 面料管理
- 面料信息管理（名称、材质类型、用途）
- 支持材质类型：细帆、细帆绗棉、缎面绗棉
- 用途分类：表布、里布
- 筛选和搜索功能

### 👜 包型管理
- 多级分类系统
- 包型信息管理（名称、价格、图片、视频）
- 自定义分类结构
- 分类层级管理

### 📦 库存管理
- 现货商品 CRUD 操作
- 库存数量实时更新
- 库存预警系统
- 商品搜索功能

### 📋 订单管理
- 分步骤创建订单
- 支持现货和定制商品
- 自动库存扣减
- 订单状态管理
- 客户积分自动更新

### 🚀 性能优化
- **智能缓存系统**：多层缓存机制，显著提升响应速度
- **数据库优化**：自动索引创建、查询优化、连接池管理
- **批量操作**：支持批量数据导入导出，提高处理效率
- **性能监控**：实时监控系统性能，自动生成性能报告

### 📊 日志管理
- **统一日志系统**：集中管理所有模块日志
- **多级别日志**：DEBUG、INFO、WARNING、ERROR、CRITICAL
- **日志分析**：可视化日志统计和趋势分析
- **实时监控**：实时错误监控和告警

### 🔧 系统管理
- **自动备份**：定期自动备份数据库
- **系统设置**：灵活的系统配置管理
- **异常处理**：全局异常捕获和处理机制

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Windows/macOS/Linux

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd My_Todo
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行应用**
   ```bash
   streamlit run main.py
   ```

4. **访问应用**
   打开浏览器访问：http://localhost:8501

## 📁 项目结构

```
星之梦手作管理系统/
├── main.py                          # 🚀 主应用程序入口
├── database.py                      # 🗄️ 数据库管理核心
├── config.py                        # ⚙️ 系统配置管理
├── requirements.txt                 # 📦 项目依赖清单
├── README.md                       # 📖 项目说明文档
├── 
├── 📂 核心模块/
│   ├── services.py                 # 🔧 业务服务层
│   ├── auto_backup.py              # 💾 自动备份系统
│   ├── batch_operations.py         # 📊 批量操作处理
│   ├── cache_manager.py            # 🚀 缓存管理系统
│   ├── performance_monitor.py      # 📈 性能监控模块
│   └── database_optimizer.py       # ⚡ 数据库优化器
│
├── 📂 用户界面/
│   ├── ui_components.py            # 🎨 基础UI组件
│   ├── ui_components_extended.py   # 🎨 扩展UI组件
│   ├── upload_components.py        # 📤 文件上传组件
│   └── enhanced_log_viewer.py      # 📊 增强日志查看器
│
├── 📂 工具模块/
│   └── utils/
│       ├── logger.py               # 📝 统一日志系统
│       ├── exception_handler.py    # ⚠️ 异常处理器
│       └── state_manager.py        # 🔄 状态管理器
│
├── 📂 数据文件/
│   ├── business_management.db      # 🗄️ 主数据库（自动生成）
│   ├── logs/                       # 📝 日志文件目录
│   │   ├── app.log                # 📋 应用日志
│   │   ├── error.log              # ❌ 错误日志
│   │   ├── performance.log        # 📈 性能日志
│   │   └── database.log           # 🗄️ 数据库日志
│   └── uploads/                    # 📤 上传文件目录
│
└── 📂 文档/
    ├── API_Documentation.md        # 📚 API文档
    ├── Deployment_Guide.md         # 🚀 部署指南
    └── User_Manual.md              # 👥 用户手册
```

## 🎯 使用指南

### 初次使用
1. 启动应用后，系统会自动创建数据库
2. 建议按以下顺序设置：
   - 添加客户信息
   - 创建包型分类
   - 添加面料信息
   - 添加包型
   - 添加库存商品
   - 创建订单

### 订单流程
1. **选择客户**：从现有客户中选择或新建客户
2. **添加商品**：
   - 现货商品：直接从库存中选择
   - 定制商品：选择包型、表布、里布
3. **确认订单**：添加备注信息并创建订单
4. **完成支付**：标记订单为已完成，自动更新客户积分

### 积分系统
- 每支付 1 元获得 1 积分
- 订单完成支付后自动更新客户积分
- 支持手动调整客户积分

## 🛠️ 技术栈

### 核心框架
- **前端框架**：Streamlit 1.28+
- **数据库**：SQLite 3.0+
- **数据处理**：Pandas 2.0+
- **图表展示**：Plotly 5.0+

### UI 组件
- **导航组件**：streamlit-option-menu
- **数据表格**：streamlit-aggrid
- **文件上传**：自定义拖拽上传组件
- **响应式布局**：自适应多设备显示

### 性能优化
- **缓存系统**：Streamlit Cache + 自定义缓存管理器
- **数据库优化**：SQLite 索引优化、查询优化
- **异步处理**：批量操作异步处理
- **内存管理**：智能内存清理和状态管理

### 监控与日志
- **日志系统**：Python logging + 自定义日志管理器
- **性能监控**：实时性能指标收集
- **异常处理**：全局异常捕获和处理
- **系统监控**：缓存使用率、数据库性能监控

### 开发工具
- **代码质量**：类型提示、文档字符串
- **错误处理**：装饰器模式异常处理
- **配置管理**：集中化配置系统
- **自动化**：自动备份、自动优化

## 📈 系统特点

### 🎨 现代化 UI/UX
- 响应式设计
- 直观的导航系统
- 美观的数据展示
- 友好的用户交互

### 🔒 数据安全
- 本地 SQLite 数据库
- 数据完整性约束
- 事务处理保证

### ⚡ 高性能
- 缓存机制优化
- 实时数据更新
- 快速搜索功能

### 🔧 易于扩展
- 模块化设计
- 清晰的代码结构
- 易于添加新功能

## 📚 文档

- **[API 文档](docs/API_Documentation.md)** - 详细的 API 接口说明
- **[部署指南](docs/Deployment_Guide.md)** - 生产环境部署指导
- **[用户手册](docs/User_Manual.md)** - 完整的用户操作指南
- **[性能优化指南](docs/Performance_Guide.md)** - 系统性能优化建议

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来改进这个项目！

### 贡献流程
1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发规范
- 遵循 PEP 8 代码规范
- 添加适当的类型提示
- 编写清晰的文档字符串
- 确保所有测试通过

## 📄 许可证

本项目采用 MIT 许可证。

## 📞 支持

如有问题或建议，请通过以下方式联系：
- 提交 GitHub Issue
- 发送邮件至：[your-email@example.com]

---

**让生意管理更简单高效！** 🚀
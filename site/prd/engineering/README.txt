结构生物学通用计算Agent · 工程合同包 v0.2

用途：在实现前审查接口、数据、执行协议与验收落点；不是可启动的Agent应用。

内容：contracts/openapi.json、API/Worker/能力包Schema、合成JSON示例、PostgreSQL迁移草案、ops/config.example.yaml、完整工程规格与静态校验报告。

开发顺序：
1. 主PRD： http://172.16.4.5:3188/prd/
2. 工程规格： http://172.16.4.5:3188/prd/engineering/
3. 按ENG-01至ENG-12依赖拆Issue，FR/AC与工程测试保留关联。
4. 在独立测试数据库/隔离运行环境完成迁移、并发、身份、文件与进程恢复验证，再配置真实模型先导。

重要边界：
- 当前3188仅为静态资料站，不提供合同中的执行API。
- SQL未应用；语法/引用检查不代表触发器、权限或事务已实测。
- 示例synthetic，非本次Agent运行。TaskSpec文档标记不属于生产DTO，具体见schema。
- 配置mode=design_only、active_agent_api_enabled=false，不含凭证；必须实现应用和严格配置加载器后才可启用。
- 原始AdK（腺苷酸激酶）坐标及数值仅作参考，不能代表通用Agent性能。

离线合同校验（需要独立Python环境）：
  python -m pip install -r validation/requirements.txt
  python validation/check_contracts.py

这只运行静态合同/示例/SQL解析检查，不启动API、数据库或模型，也不安装科学工具。

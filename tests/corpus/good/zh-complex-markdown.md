# pipeline-runner

流水线执行器的配置与嵌套示例。

## 嵌入脚本

文档里引用的校验脚本本身包含围栏，外层用四反引号包裹：

````markdown
按顺序执行：

```bash
pipeline-runner validate --stage build
pipeline-runner validate --stage deploy
```

两步都返回 0 才算通过。
````

## 排除项

<!-- 维护者注释：changelog 由 CI 生成，不手写。 -->

正则示例里的感叹号不属于文档正文，`a != b` 写在行内代码里。

更多参数见 [CLI 手册][cli-manual]，路径规则见 [路径约定][paths]。

[cli-manual]: https://example.com/docs/cli
[paths]: https://example.com/docs/paths

## 状态

运行中任务可以在表格里看到阶段与重试次数，字段名与 `--output json` 输出一致。

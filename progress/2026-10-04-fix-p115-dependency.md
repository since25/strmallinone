## 2026-10-04 - Task: Fix unavailable p115client deployment dependency

### What was done

- 将后端镜像依赖从不存在的 `p115client==0.0.8.5.1.1` 调整为 PyPI 可用的 `0.0.9.7.2`。
- 核对新版本仍提供当前 adapter 使用的 `P115Client`、目录、分享读取和分享转存接口。

### Testing

- `python3 -m pip index versions p115client`：确认 `0.0.9.7.2` 可用。
- 下载 wheel 并检查接口符号：`P115Client`、`fs_files`、`fs_mkdir`、`fs_dir_getid`、`share_snap`、`share_receive` 均存在。
- 上一次远端 Docker 构建因旧版本不存在失败；修复后尚未重新构建。

### Notes

Changed files:
- `backend_py/requirements.txt`: 更新可安装的 p115client 固定版本。

Rollback:
- 将 `backend_py/requirements.txt` 中版本恢复为提交前值即可；该旧版本无法从当前 PyPI 索引安装。

"""Cloud runner with a Beijing time window and an optional read-only check."""
import os
from datetime import datetime, timedelta, timezone

from .check_in import STATUS_MESSAGES, check_in_with_retry
from .get_info import get_token, get_transition_today

BEIJING = timezone(timedelta(hours=8))


def may_submit(now: datetime, expected_date: str = "") -> bool:
    local = now.astimezone(BEIJING)
    minute = local.hour * 60 + local.minute
    return (21 * 60 <= minute < 23 * 60 + 25
            and (not expected_date or expected_date == local.date().isoformat()))


def main() -> int:
    diagnostic = os.getenv("SWUDK_DIAGNOSTIC") == "1"
    now = datetime.now(BEIJING)
    print(f"北京时间：{now:%Y-%m-%d %H:%M:%S}")
    if not diagnostic and not may_submit(now, os.getenv("SWUDK_EXPECTED_DATE", "")):
        print("未执行：已超出本次任务的日期或打卡时段，防止跨天运行。")
        return 1
    username = os.getenv("SWUDK_USERNAME", "").strip()
    password = os.getenv("SWUDK_PASSWORD", "")
    if not username or not password:
        print("校园账号配置不完整。")
        return 1
    if diagnostic:
        token = get_token(username, password, 15)
        if not token:
            print("只读检查：学校登录未成功。未提交签到。")
            return 1
        transition = get_transition_today(token, 15)
        print("只读检查：学校登录成功。")
        if not transition:
            print("学校没有返回当天任务。未提交签到。")
        elif transition.get("qdzt") == "已签到":
            print("学校显示当天已签到。未重复提交。")
        else:
            print("查到当天任务，尚未签到。只读检查没有提交。")
        return 0
    result = check_in_with_retry(username, password, timeout=15)
    print(f"[{result}] {STATUS_MESSAGES.get(result, '未知结果')}")
    return 0 if result in {1, 2, 5} else 1


if __name__ == "__main__":
    raise SystemExit(main())


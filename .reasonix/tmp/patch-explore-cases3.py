# -*- coding: utf-8 -*-
"""补丁3：修正 tc09（关键字卡片验证）与 tc10（500 缺陷判定）"""
import io

path = ".reasonix/tmp/explore-cases-v1.py"
src = io.open(path, encoding="utf-8").read()

# tc09 验证逻辑
old9 = '''            try:
                sb = page.locator("input[placeholder='搜索关键字名称...']")
                sb.fill(KW)
                sb.press("Enter")
                page.wait_for_timeout(1000)
                tbody = clean(page.locator(".el-table__body").first.inner_text()) if page.locator(".el-table__body").count() else ""
                r["result"] = f"toast={toasts}；表含kw={KW in tbody}；代码展示={'def' in tbody}"
                r["verdict"] = "PASS" if KW in tbody else "PARTIAL"
            except Exception as e:
                r["result"] = f"toast={toasts}；列表验证异常: {str(e)[:100]}"; r["verdict"] = "PARTIAL"'''
new9 = '''            try:
                sb = page.locator("input[placeholder='搜索关键字名称...']")
                sb.fill(KW)
                sb.press("Enter")
                page.wait_for_timeout(1000)
                card_txt = ""
                cards = page.locator(".keyword-card")
                for i in range(cards.count()):
                    ct = clean(cards.nth(i).inner_text())
                    if KW in ct:
                        card_txt = ct
                        break
                r["hints"].append("关键字列表为 .keyword-card 卡片结构")
                r["result"] = f"toast={toasts}；关键字卡片含kw={KW in card_txt}；代码展示={'def' in card_txt}"
                r["verdict"] = "PASS" if (KW in card_txt and "def" in card_txt) else "PARTIAL"
            except Exception as e:
                r["result"] = f"toast={toasts}；列表验证异常: {str(e)[:100]}"; r["verdict"] = "PARTIAL"'''
assert old9 in src, "tc09 锚点未找到"
src = src.replace(old9, new9)

# tc10 判定逻辑
old10 = '''            click_scope_button(page, dlg, "确认创建")
            page.wait_for_timeout(1800)
            toasts = grab_toasts(page)
            r["hints"].append("toast=" + json.dumps(toasts, ensure_ascii=False))
            try:
                tbody = clean(page.locator(".el-table__body").first.inner_text()) if page.locator(".el-table__body").count() else ""
                r["result"] = f"toast={toasts}；表含sched={SCHED in tbody}、cron={'0 8 * * *' in tbody}、套件={SUITE in tbody}、启用={'启用' in tbody}"
                r["verdict"] = "PASS" if (SCHED in tbody and SUITE in tbody) else "PARTIAL"
            except Exception as e:
                r["result"] = f"toast={toasts}；列表验证异常: {str(e)[:100]}"; r["verdict"] = "PARTIAL"'''
new10 = '''            click_scope_button(page, dlg, "确认创建")
            page.wait_for_timeout(1800)
            toasts = grab_toasts(page)
            r["hints"].append("toast=" + json.dumps(toasts, ensure_ascii=False))
            sched500 = any(("schedules" in a["url"] and a["status"] == 500) for a in api_log[s0:])
            if sched500 or any("服务器内部错误" in t for t in toasts):
                r["result"] = f"缺陷复现：新建定时任务 POST /schedules 500 服务器内部错误；toast={toasts}；任务未创建"
                r["verdict"] = "FAIL"
                r["hints"].insert(0, "缺陷：新建定时任务返回 500 服务器内部错误（cron 变体均复现，与参数无关）")
            else:
                try:
                    tbody = clean(page.locator(".el-table__body").first.inner_text()) if page.locator(".el-table__body").count() else ""
                    r["result"] = f"toast={toasts}；表含sched={SCHED in tbody}、cron={'0 8 * * *' in tbody}、套件={SUITE in tbody}、启用={'启用' in tbody}"
                    r["verdict"] = "PASS" if (SCHED in tbody and SUITE in tbody) else "PARTIAL"
                except Exception as e:
                    r["result"] = f"toast={toasts}；列表验证异常: {str(e)[:100]}"; r["verdict"] = "PARTIAL"'''
assert old10 in src, "tc10 锚点未找到"
src = src.replace(old10, new10)

io.open(path, "w", encoding="utf-8").write(src)
print("补丁3完成")
